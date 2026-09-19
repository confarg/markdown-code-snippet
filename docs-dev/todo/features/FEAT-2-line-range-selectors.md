# FEAT-2 — Select a line range, GitHub-style

**Where:** `src/markdown_code_snippet/_extract/`
**Filed:** 2026-09-20
**Effort:** S · **Risk:** medium · **Impact:** behavior

`<!-- snippet: setup.sh#L4-L9 -->`, and `#L4` for a single line. Trivial behind the dispatch in
`_extract/__init__.py`, and the only selector that works on any file at all.

Worth thinking about before adding, rather than after: a line range is the one selector kind that
goes silently wrong. Insert a line above the range and the documentation shows something else, with
nothing to report and no test that could fail. Named regions (FEAT-1) do not have that property, so
the honest question is whether shipping ranges makes regions less likely to be used where they
should be. The trade-off is sketched in
[06-design-decisions.md#whole-files-and-python-symbols-only](../../architecture/06-design-decisions.md#whole-files-and-python-symbols-only).
