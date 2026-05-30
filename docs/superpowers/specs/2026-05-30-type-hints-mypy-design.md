# Type hints + mypy across scraper modules (issue #13)

## Goal

Add complete type signatures across `scraper/` and wire mypy into pre-commit so type drift is caught. Today `http.py` is fully typed, `user.py`/`books.py`/`shelves.py` have partial param hints but few return types, and `author.py` is unannotated.

## Decisions

- **Checker:** mypy (official pure-Python pre-commit hook; fits the existing pip dev-deps + pre-commit/CI setup; no Node dependency).
- **Strictness:** pragmatic — enforce complete signatures (`disallow_untyped_defs`) with Optional/None safety on, but skip the rest of the full `strict` suite. Real drift protection, minimal noise.
- **Optional dereferences:** centralize narrowing in small typed helpers rather than scattering `assert`/`isinstance`/`# type: ignore` at every call site.

## 1. Tooling & config

`pyproject.toml` — add `[tool.mypy]` (shared by the pre-commit hook and local/editor runs):

```toml
[tool.mypy]
python_version = "3.10"
files = ["scraper"]
disallow_untyped_defs = true
```

`.pre-commit-config.yaml` — add the `mirrors-mypy` hook with `additional_dependencies = ["beautifulsoup4", "aiohttp", "rich"]` so it resolves third-party types inside pre-commit's isolated venv. CI already runs `pre-commit/action`, so this lands in CI automatically — no workflow edits.

`pyproject.toml` `[project.optional-dependencies].dev` — add `mypy` for local runs.

## 2. Narrowing helpers — new `scraper/parse.py`

bs4's `.find()` returns `Tag | NavigableString | None`, so a direct `soup.find(...).text` fails Optional-safe mypy. Two small typed helpers centralize the narrowing so call sites stay clean:

- `find_tag(node, ...) -> Tag` — for **required** elements; raises a clear "element not found" error instead of today's cryptic `AttributeError: 'NoneType'`.
- `find_tag_opt(node, ...) -> Tag | None` — for legitimate optional sites that already branch on `if cell:`.

`.find_all()` already returns a list (elements typed `Any`) and needs no helper. Attribute reads (`.get("href")`/`.attrs.get("src")` → `str | list[str] | None`) are narrowed inline, or via one tiny `attr_str(tag, name) -> str | None` helper if the pattern recurs enough to justify it (decided during implementation).

## 3. Annotation plan (per module)

- **`author.py`** — unannotated today; add signatures throughout. `_tasks: dict[str, asyncio.Task[dict]]`. `get_id_number`/`scrape_author`/`_scrape_author` take `str`; extraction helpers return `str | None`; scrape funcs return `dict[str, Any]`.
- **`user.py`** — add return types: `get_user_name -> str`, `get_num_ratings -> int`, `get_avg_rating -> float`, `get_num_reviews -> int`, `get_user_info -> BeautifulSoup | None`.
- **`books.py`** — add return types: required extractors return `str`/`int`/`float`, optional extractors return `... | None`; `get_id -> str`; `scrape_book -> dict[str, Any]`.
- **`shelves.py`** — row helpers take `Tag` and return `str`/`int | None`/`list[str]`; `make_progress -> Progress`; `fetch_shelf_page -> BeautifulSoup`; `collect_shelf_rows -> list[Tag]`; `_dedupe_books(shelf_rows: list[tuple[str, list[Tag]]]) -> dict[str, dict]`.
- **`__main__.py`** — add the missing returns: `scrape_user -> int`, `main -> None`.
- **`http.py`** — already typed, but `get_html` trips mypy's "missing return" (mypy can't prove the retry loop runs), so the final `raise FetchError(url)` moves to just after the loop. Behavior-preserving.

## 4. re.search narrowing

`re.search(...).group()` returns `Match | None`. The few sites (`get_id_number`, `books.get_id`, `get_num_pages`, `get_year_first_published`, shelf-name parsing) get inline `assert ... is not None` or light restructuring — no helper.

## 5. Verification

- `pre-commit run mypy --all-files` passes clean.
- Existing `pytest` suite stays green. The helper swap and the `http.py` tweak are behavior-preserving, except missing required elements now raise a clear error instead of `AttributeError: 'NoneType'`.

## Scope

mypy checks `scraper/` only. `tests/` is out of scope per the issue and could be a follow-up.
