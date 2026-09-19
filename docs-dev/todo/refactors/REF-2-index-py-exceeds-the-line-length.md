# REF-2 — `docs-dev/todo/index.py` does not satisfy the project's own lint rules

**Where:** `docs-dev/todo/index.py`
**Filed:** 2026-09-20
**Effort:** S · **Risk:** low · **Impact:** none

31 `E501` violations: the file was written at a wider margin than the 80 columns `.ruff.toml` sets,
so `uv run pre-commit run --all-files` cannot come back clean while it is there, and `ruff format`
rewrites 14 of its lines into 57 the moment it is allowed to.

Two ways to close it, and they are genuinely different decisions rather than the same one twice:

- Rewrap the file to 80 columns and let the formatter own it. Consistent, and the board tooling then
  reads like the rest of the tree.
- Exclude `docs-dev/` from the lint configuration. It is internal tooling rather than shipped code,
  and its long f-strings building table rows are more legible unwrapped than split.

Left as a ticket rather than fixed in passing: it is not part of any task that has come up, and
reformatting a file nobody asked about is how an unrelated diff gets into a change.

```console
$ uvx ruff check docs-dev/todo/index.py --output-format=concise | tail -2
docs-dev\todo\index.py:190:81: E501 Line too long (117 > 80)
Found 31 errors.
```
