# Async/aiohttp rewrite — design

GitHub issue: [#11](https://github.com/YashTotale/goodreads-user-scraper/issues/11)

## Goal

Replace the synchronous `requests` + `ThreadPoolExecutor` scraper with an
`asyncio` + `aiohttp` implementation to cut wall-clock time on large libraries,
while keeping concurrency courteous and behavior identical.

## Decisions

- **Sequential shelves, concurrent rows (approach A).** Shelves still iterate
  one at a time so the cross-shelf dedup invariant holds (a book already on disk
  from an earlier shelf takes the cheap append-shelf path). Concurrency lives in
  the row/book/author fetches. Approach B (parallel shelves) is deferred behind
  the measurement.
- **In-flight task map for authors (approach B).** Concurrent callers wanting the
  same author await one shared `asyncio.Task` instead of each missing a plain
  dict cache and re-fetching.
- **Single global semaphore** in `http.py` (`MAX_CONCURRENCY = 32`, top of the
  issue's 16–32 band). Not a CLI flag. Set to 32 after measurement: 16 barely beat
  the old 8-thread pool, while 32 ran ~1.7× faster with no errors or auth failures.

## Changes by module

### `scraper/http.py`
- `aiohttp.ClientSession` replaces `requests.Session`; same `init_session(cookie)`
  / `has_cookie()` shape. Add module-global `asyncio.Semaphore(MAX_CONCURRENCY)`.
- `get_html` / `get_soup` become coroutines: acquire the semaphore, `await`
  the request, `raise_for_status()`, `await resp.text()`. Auth-failure detection
  and the `sys.exit` on a bad cookie are unchanged.
- Add `async def close_session()`.

### `scraper/__main__.py`
- `main()` stays sync (argparse, `mkdir`, `resolve_cookie` unchanged), then
  `asyncio.run(scrape_user(args, cookie))`.
- `scrape_user` becomes async: `init_session` (inside the loop), await user info
  and shelves, `close_session()` in a `finally`.

### `scraper/shelves.py`
- Delete `ThreadPoolExecutor` and `MAX_WORKERS`.
- `get_shelf` keeps the sequential page loop (needed for end detection) but
  replaces per-page submission with `await asyncio.gather(*(_process_row(...)))` —
  matches the old per-page barrier.
- `fetch_shelf_page`, `_process_row`, `get_all_shelves` become async; shelves
  still iterate sequentially.

### `scraper/books.py` / `scraper/user.py`
- `scrape_book` and `get_user_info` become async (`await http.get_soup`). Pure
  `get_*` parsers (soup in, no I/O) stay sync and untouched.

### `scraper/author.py`
- `_cache: dict` → `_tasks: dict[str, asyncio.Task]`. `scrape_author` stores/awaits
  a shared task; `_scrape_author` holds the existing fetch+parse body.

## Tests
- Add `pytest-asyncio` (dev) and `asyncio_mode = "auto"`.
- `conftest.py`: `mock_get_soup`'s inner `fake` becomes async; `_clear_author_cache`
  clears `author._tasks`.
- Orchestrator tests awaiting a coroutine become `async def` (`test_author`,
  `test_books`, `test_user`, `test_shelves`); mocked `get_shelf` becomes async.
- Unchanged: pure-parser tests, `test_http.py`, `test_main.py` (CLI tests stay
  sync — `main()` owns the loop).

## Packaging
- `pyproject.toml`: `requests` → `aiohttp` in dependencies; add `pytest-asyncio`
  to `dev`; add `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`.
- No CLI changes, no new flags. README: no user-facing change expected.

## Measurement

Live scrape of user `54739262` with cookie, each into a fresh output dir (93
books, 14 shelves). Single samples, so subject to network variance.

| Variant | Wall-clock |
|---|---|
| Baseline (sync, `ThreadPoolExecutor(8)`) | 89.3 s |
| Async, concurrency 16 | 86.4 s |
| Async, concurrency 32 | ~53 s |

**Net: ~1.7× faster at concurrency 32.** Not the hypothesized 2–4×, for two
reasons surfaced by the measurement:

- **A ~31.5 s serial floor.** Re-running into the populated dir (no book scraping,
  only profile + shelf-page fetches) took 31.5 s — 14 shelves fetched
  sequentially, each paginated sequentially, ~1 s/request. Approach A cannot
  reduce this; it's ~58% of the concurrency-32 run.
- **Concurrency 16 was too low.** It only modestly beats 8-way threads, and the
  serial floor dilutes the gain. 32 shrinks the book-scraping portion enough to
  show a clear win, and Goodreads tolerated it cleanly (no throttling observed).

**Follow-up lever:** the serial shelf-page chain is exactly what approach B
(parallel shelves) would attack. A 100%-safe form: fetch all shelf listing pages
concurrently, dedupe `(book, shelves)` by `book_id` up front, then scrape each
unique book once. Deferred — this is the "decide if B is needed" call.
