# Retry/backoff for transient HTTP failures (issue #19)

## Problem

The async scraper funnels every request through `http.get_html`, which has no
retry. A single transient failure on a critical fetch — the profile page or a
shelf listing — propagates and aborts the whole run with a raw traceback
(observed: `asyncio.TimeoutError` on the first request during Goodreads
throttling).

Already handled, out of scope:
- Per-book failures are caught and logged in `process_book` (run continues).
- Author fetches drop a failed task from the cache so it can be retried.

The gap is the HTTP layer itself: transient timeouts / `429` / `5xx` are fatal
on critical fetches and silently skip books elsewhere.

## Goal

Wrap `get_html` with bounded retry + exponential backoff (with jitter) on
transient errors, staying courteous (no retry storm), and fail critical fetches
with a readable message instead of a stack trace.

## Decisions

- **Config:** hardcoded module constants in `http.py`, no new CLI flags.
- **Retry budget:** 4 retries, base 1s → delays ≈ 1, 2, 4, 8s (jittered), ~15s
  worst case per URL.
- **Sleep cap:** 30s per sleep; also caps a server-sent `Retry-After`.
- **Exit model:** exhausted retries raise `FetchError`; critical fetches exit
  cleanly at the top level, book/author fetches keep their existing skip path.

## Design

All changes live in `scraper/http.py` plus a one-line catch in
`scraper/__main__.py`. No caller signatures change.

### Constants (`http.py`)

```python
MAX_RETRIES = 4
BACKOFF_BASE = 1.0   # seconds
MAX_BACKOFF = 30.0   # cap per sleep, also caps Retry-After
```

### Transient classification

Retry on:
- `asyncio.TimeoutError`
- `aiohttp.ClientConnectionError`
- HTTP status `429`
- HTTP status `5xx`

Do not retry on other `4xx` (404/403/…): `raise_for_status()` raises and the
error propagates as it does today.

### `get_html` retry loop

The retry loop stays **inside `async with _semaphore`**, so backoff sleeps while
holding the concurrency slot. Under a `429` storm, in-flight requests collapse
toward zero concurrency and resume staggered by jitter — this is the
"respects the semaphore / no retry storm" behavior.

Per attempt:
1. Issue the request.
2. Non-transient status → `raise_for_status()` then return body (success path).
3. Transient status → read `Retry-After` (integer seconds) if present.
4. Transient exception → use computed backoff.
5. On the final attempt, raise `FetchError(url)`.
6. Otherwise sleep, then retry.

Backoff: `min(MAX_BACKOFF, BACKOFF_BASE * 2 ** attempt)` with full jitter
(`random.uniform(0, delay)`). A present `Retry-After` is used instead, capped at
`MAX_BACKOFF`.

Small pure helpers keep the loop readable and testable:
- `_parse_retry_after(header)` → seconds or `None` (ignores non-integer/date forms)
- `_backoff(attempt)` → jittered, capped delay
- transient-status check

### `FetchError`

A small `Exception` subclass carrying the URL and a readable reason, e.g.:

```
Failed to fetch {url} after 4 retries — Goodreads may be rate-limiting; try again later.
```

### Graceful exit (`__main__.py`)

Wrap the top-level run so retry exhaustion on a critical fetch exits cleanly:

```python
try:
    asyncio.run(scrape_user(args, cookie))
except http.FetchError as e:
    sys.exit(f"❌ {e}")
```

`scrape_user`'s existing `finally` still closes the session first. Book/author
exhaustion is unchanged: `process_book`'s `except` logs `⚠️ Skipped …` and the
run continues. This mirrors the existing cookie-failure `sys.exit` pattern.

## Testing (`tests/test_http.py`)

Offline tests with a fake `_session` (an async context manager yielding fake
responses) and a monkeypatched `asyncio.sleep` so no real time passes:

- transient status (429/503) then success → retried, returns body, slept between
- timeout exception then success → retried
- exhausted retries → raises `FetchError`
- non-transient `4xx` (404) → raises immediately, no retry
- `Retry-After` honored and capped at `MAX_BACKOFF`
- pure helpers (`_backoff`, `_parse_retry_after`, transient check) tested directly

## README

One bullet in **Troubleshooting**: the scraper auto-retries transient
rate-limit/timeout errors with backoff and exits cleanly if Goodreads stays
unavailable. No new arguments to document.

## Acceptance criteria

- A transient timeout/`429`/`5xx` on a discovery or book/author fetch is retried
  and the run completes.
- Exhausted retries fail gracefully with a readable message, not a raw traceback.
- Concurrency stays courteous (no retry storm).
