# FEAT-5 — A `[tool.markdown-code-snippet]` table in pyproject.toml

**Where:** `src/markdown_code_snippet/_cli.py`
**Filed:** 2026-09-20
**Effort:** M *(design pass; implementation not sized)*
**Risk:** low · **Impact:** behavior

`--root` is the only setting the tool has, and a flag carries it
([06-design-decisions.md#no-configuration-file-in-v1](../../architecture/06-design-decisions.md#no-configuration-file-in-v1)).
A configuration table becomes worth its cost once there is a second setting that a repository wants
to state once rather than repeat in every hook invocation — extra entries for the extension-to-
language map is the likeliest candidate, and a default set of documents to process is another.

The design pass has to settle: where the file is discovered from (the document, the working
directory, `--root`), how a flag and a table interact when they disagree, and whether an unknown key
is an error. Filing it now so the reasoning is not rediscovered the first time someone asks for a
setting.
