# FEAT-4 — An option to include the comments above a definition

**Where:** `src/markdown_code_snippet/_extract/_python.py`, `src/markdown_code_snippet/_annotation.py`
**Filed:** 2026-09-20
**Effort:** S · **Risk:** low · **Impact:** behavior

A snippet starts at the first decorator, so the comment above a definition is dropped even when it
is the explanation a reader wants
([07-limitations.md#comments-above-a-definition-are-not-included](../../architecture/07-limitations.md#comments-above-a-definition-are-not-included)).

An option — `comments=true`, say — would walk upwards over contiguous comment lines. The reason it
is not the default is that "how far up" is a guess: one line, a block, through a blank line, past a
`#:` attribute comment belonging to something else. Deciding that is the work; the walk itself is a
few lines.

A user can always move the explanation into the docstring instead, which is included, so this is a
convenience rather than a gap.
