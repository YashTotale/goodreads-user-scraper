# Scraper progress indicators — design

**Date:** 2026-05-29
**Branch:** issue-20
**Supersedes:** GitHub issue [#20](https://github.com/YashTotale/goodreads-user-scraper/issues/20) (originally "make the shelf-scraping progress bar transient")

## Motivation

Issue #20 started narrow: the books progress bar stayed on screen after finishing,
so the final output showed both the completed bar and the summary line. We're
expanding it into a consistent progress/success pattern across all three phases of a
run — user, shelves, books — plus a closing "where's my data" footer.

Each phase shows a **transient** working state (spinner or progress bar) that clears
once complete and is replaced by a single permanent summary line with a matching emoji.

## Final output

A full run (with cookie) prints:

```
👤  Yash Totale · 81 ratings · 3 reviews

📚  14 shelves
📖  93 books
📁  Saved to /Users/you/goodreads-data
```

While working, each summary line is preceded by a transient indicator that clears on
completion:

| Phase | While working (transient) | Replaced by |
|-------|---------------------------|-------------|
| User | `⠋ Finding user…` (spinner) | `👤  {name} · {n} ratings · {n} reviews` |
| Shelves | `Finding shelves 0/14 ━━━━` (bar) | `📚  {n} shelves` |
| Books | `Scraping books 0/93 ━━━━` (bar) | `📖  {n} books` |
| Footer | — | `📁  Saved to {abs path}` |

The previous `Found {n} books across {n} shelves` line is removed: the shelf count now
lives in the shelves summary, and the book count is shown by the books bar and its
summary.

Emojis match their line item (person / stack-of-books-as-shelf / single book / folder)
and are flat monochrome glyphs at consistent visual weight. The `✅` checkmark is
dropped.

## Changes by module

### `scraper/user.py`

- Wrap the profile fetch in `console.status("Finding user…")` so a spinner shows during
  the request and clears when the `👤` line prints.
- **Return the parsed profile soup** from `get_user_info` so the shelves phase can reuse
  it. Return `None` when `--skip_user_info` is set.
- Keep the existing blank-line separator after the `👤` line (printed only when shelves
  aren't skipped), giving the one-line gap shown in the final output above.

### `scraper/__main__.py`

- `scrape_user` threads the profile through: `profile = await user.get_user_info(args)`
  then `await shelves.get_all_shelves(args, profile)`.
- After both phases, print the footer `📁  Saved to {abs path}` once, using the resolved
  absolute path (`args.output_dir.resolve()`) emitted as an OSC 8 hyperlink
  (`file://…`) so terminals that support it make it clickable.
- **Nothing-to-do guard:** in `main`, if both `--skip_user_info` and `--skip_shelves`
  are set, print `⚠️  Nothing to do: --skip_user_info and --skip_shelves are both set.`
  and return before creating the output dir or opening a session. Because that case
  exits early, `scrape_user` always prints the footer when it runs.

### `scraper/shelves.py`

- `get_all_shelves(args, profile=None)` — reuse the passed-in profile soup; only fetch
  the profile itself when `profile is None`. This removes the redundant second fetch of
  the profile page (previously fetched once in `user.py` and again here).
- Replace the `console.status("Discovering shelves…")` + bare `asyncio.gather` with a
  **transient progress bar** that advances per shelf (`Finding shelves 0/N`). The
  per-shelf coroutine returns `(shelf, rows)` tuples, fed directly to `_dedupe_books`,
  dropping the `zip(shelf_names, per_shelf)`.
- Print `📚  {n} shelves` after the bar clears.
- **Remove** the `Found {n} books across {n} shelves` line.
- Make the books progress bar **transient** (the original issue #20 fix) and change its
  summary to `📖  {n} books` (drop the `· {n} shelves` suffix).
- Factor the shared `Progress(...)` column config plus `transient=True` into one
  `make_progress()` helper used by both bars.

## Profile-fetch consolidation — skip-flag matrix

| `skip_user_info` | `skip_shelves` | cookie | Profile fetches |
|---|---|---|---|
| no | no | yes | 1 (user fetches, shelves reuses) |
| yes | no | yes | 1 (shelves fetches its own) |
| no | yes | — | 1 (user only) |
| yes | no | no | 0 (shelves returns on cookie check before fetching) |
| yes | yes | — | 0 |

The cookie check in `get_all_shelves` runs before any fetch, so the no-cookie path never
fetches a profile it won't use.

## Tests

No existing test asserts on console output strings, so the indicator/wording changes
break nothing. The signature change is backward-compatible (`profile=None` default).

- `test_get_all_shelves_dedupes_and_scrapes` — calls `get_all_shelves(args)` directly;
  with `profile=None` it fetches its own profile via the mock. Unchanged.
- `test_cli_full_run_writes_user_and_books` — threads user→shelves through `scrape_user`;
  the mock serves `profile.html` for `user/show` regardless of caller. Unchanged.
- `test_get_all_shelves_skips_without_cookie` — returns before any fetch. Unchanged.
- **New test:** when a profile soup is passed to `get_all_shelves`, it does **not**
  re-fetch `user/show` (pins the consolidation against regression).

## Out of scope

- The README demo GIF (separate paused branch) — re-rendering it with the new output is
  a follow-up, not part of this change.
- No changes to scraped data, JSON output, or CLI flags.
