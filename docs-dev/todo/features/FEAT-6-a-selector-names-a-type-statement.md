# FEAT-6 — A selector names a `type` statement

**Where:** `src/markdown_code_snippet/_extract/_python.py` · **Filed:** 2026-10-03
**Effort:** S · **Risk:** medium · **Impact:** behavior

`_defined_names` answers `ClassDef`, `FunctionDef`, `AsyncFunctionDef`, `Assign` and
`AnnAssign`, so a PEP 695 `type X = …` is invisible to a selector and fails as not defined —
one node short of the table in
[03-extraction.md#what-is-addressable](../../architecture/03-extraction.md#what-is-addressable):

```console
$ printf 'type Config = int | str\n\n\ndef main() -> None: ...\n' > type_stmt.py
$ uv run python -c "from pathlib import Path; \
from markdown_code_snippet._extract._python import extract_symbol; \
extract_symbol(Path('type_stmt.py'), 'Config')"
SelectorNotFound: type_stmt.py defines no 'Config'; available here: main
```

`ast.TypeAlias` binds `node.name`, and its span is the statement itself; nothing else in
`_python.py` asks which node kinds a selector can name. Python 3.12+ parses the statement.

Motivating case: confarg's REF-59 — two blocks under its `examples/` quote
`type Config = A | B` and stay hand-copied because `#Config` cannot reach the statement.
Annotating both is the last mechanical step of that ticket, once a release carrying this is
pinned there.
