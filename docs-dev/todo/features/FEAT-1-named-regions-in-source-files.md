# FEAT-1 — Extract a named region marked out by comments in the source file

**Where:** `src/markdown_code_snippet/_extract/`
**Filed:** 2026-09-20
**Effort:** M · **Risk:** medium · **Impact:** behavior

Marker comments in a source file delimit a span, and a selector names it:
`<!-- snippet: config.yaml#server -->` for a file containing `# [snippet: server]` … `# [/snippet]`.

This is the only way to show *part* of a file that is not Python, which today is all-or-nothing
([07-limitations.md#only-python-has-symbol-selectors](../../architecture/07-limitations.md#only-python-has-symbol-selectors)).
Markers survive edits above and below them, which is what makes them preferable to line ranges
(FEAT-2).

Open questions for the design pass: which comment syntaxes to recognize (`#`, `//`, `<!-- -->`,
`;`, `--`), whether the marker lines themselves are stripped from the output, and whether a region
may nest inside another. It goes behind the dispatch in `_extract/__init__.py`, so nothing in the
scanner or the renderer changes.
