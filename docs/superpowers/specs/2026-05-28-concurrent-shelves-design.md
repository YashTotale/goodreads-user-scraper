# Concurrent shelves + rich progress — design

Follow-up to the async rewrite ([#11](https://github.com/YashTotale/goodreads-user-scraper/issues/11)).

## Goal

Collapse the sequential shelf-discovery chain (~18.6 s of a ~40 s run) by fetching
all shelf listings concurrently and scraping each unique book once. Expected:
~40 s → ~24 s (≈3.7× over the 89 s sync baseline), with book-scraping concurrency
as the floor. Replace the per-shelf CLI output with a `rich` progress bar.

## Pipeline restructure (inside `shelves.get_all_shelves`)

Three phases replace the sequential shelf loop:

- **Discover** — fetch profile, parse the shelf links (unchanged).
- **Collect** — fetch all shelf listings concurrently (`asyncio.gather`, one task per
  shelf). Each shelf still paginates internally with `per_page=100` + early
  termination. Returns rows of `(book_id, shelf, rating, dates_read)`.
- **Dedupe** — merge rows by `book_id` into
  `{ book_id: {"shelves": [...], "rating", "dates_read"} }`. Shelves accumulate in
  profile order; rating/dates come from the first row seen (book-level, identical
  across shelves).
- **Scrape** — `gather` over unique books; each scraped once, written with its full
  shelf set.

New functions replace `get_shelf` / `_process_row`:

- `collect_shelf_rows(user_id, shelf)` — paginate one shelf, return its rows.
- `process_book(book_id, info, args, output_dir)` — scrape-or-merge one book.

No file-write race: each book is touched exactly once. `__main__.py` and `user.py`
are untouched; the restructure is entirely in `shelves.py`.

## Behavior preserved

- **Dedup:** a book on `read` + `2024` → one JSON with `shelves: ["read", "2024"]`.
- **Incremental re-runs:** existing book JSON is not re-scraped — new shelves are
  merged in. Re-runs stay fast (listings + file merges only).
- **Shelf order:** profile order, same as today (Collect results iterated in
  shelf-link order during Dedupe).
- **Append-only shelves:** shelves are only added, never removed (same as today).

## CLI output (`rich`)

`rich` is confined to `shelves.py` via a module-level `Console`. User-info prints its
plain `👤 Scraped user` line first (sequential, before the bar — no console conflict).

- **Collect:** `console.status("Discovering shelves…")` spinner, then
  `Found N books across M shelves`.
- **Scrape:** `Progress` bar (spinner · description · bar · `M/N` · percent · elapsed),
  advanced per book. Per-book `🎉 Scraped`/`✅ Updated` lines are removed.
- **Skips/errors:** printed above the bar via `progress.console.print`.
- **Done:** `✅ N books · M shelves`.
- Non-TTY (CI `scripts/test.sh`) auto-degrades to plain output.

## Error handling

Per-book failures stay caught in `process_book` (logged above the bar; bar still
advances). Discovery/listing fetch failures propagate and abort — retry/backoff
robustness is deferred to a later pass.

## Non-goals

- Sharing the profile fetch between user-info and shelf-discovery (~1 s). Left as two
  fetches to keep the modules decoupled.
- Raising concurrency past 32 (already tripped Goodreads' rate limiter there).

## Dependencies, testing

- Add `rich` to `dependencies` in `pyproject.toml` (accepting its transitive deps).
- TDD: rework the `shelves` tests — pagination tests retarget to `collect_shelf_rows`,
  processing tests to `process_book`, plus a new dedup test (one book on two shelves →
  single record with both shelves). `test_main`, `user`, `books`, `author`, `http`
  tests are unaffected.

## Measurement

Re-run `scripts/test.sh` (fresh dir) once the rate limit clears; compare to the
~40 s pre-change run and the 89 s sync baseline.
