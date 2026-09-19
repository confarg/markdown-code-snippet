# Architecture notes

Internal notes for contributors and coding agents, part of [`docs-dev/`](../README.md).
They are deliberately **not** published: they name private symbols, open questions and known deviations from the intended behavior. Publishing them
(for instance as an "Internals" section copied into the site at build time) is to be reconsidered once the library ships.

These documents are the **single source of truth for the "why"**: design choices,
rationale, rejected alternatives, trade-offs and limitations. The code and its docstrings
describe _what_ things do; they must not repeat the reasoning kept here. When a rationale
changes, change it here.

Work that is still _open_ — bugs, missing features, refactors, questions for the
maintainer — lives on the boards in [`../todo/`](../todo/README.md), not in these notes. A
ticket describes work to do; closing it usually leaves a decision, and the decision comes
back here.

## Conventions

Docstrings point here through a `Dev Notes:` section, e.g.

```python
def fence_length(body: str, char: str) -> int:
    """Return how many fence characters the body needs to stay enclosed.

    Dev Notes:
        docs-dev/architecture/02-scanning-and-splicing.md#fence-escalation
    """
```

The section is hidden on the documentation site, so it is written for whoever works
on the library rather than for whoever uses it. A citation names one document and one `##` heading
anchor; headings in these files are kept stable for that reason, and renaming one means fixing
the citations that name it (`grep -rn "<old-anchor>" src/`).

Open the topic documents that match the code you are touching; the reading guide below maps
source modules to documents.

## Reading guide

| If you touch…                            | Read                                                                                            |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------- |
| anything at all                          | [05-invariants.md](05-invariants.md)                                                            |
| `_annotation.py`                         | [01-annotation-syntax.md](01-annotation-syntax.md)                                              |
| `_document.py`, `_render.py`, `_text.py` | [02-scanning-and-splicing.md](02-scanning-and-splicing.md)                                      |
| `_extract/**`, `_lang.py`                | [03-extraction.md](03-extraction.md)                                                            |
| `_resolve.py`                            | [04-paths.md](04-paths.md)                                                                      |
| `_process.py`, `_cli.py`, `__init__.py`  | [05-invariants.md](05-invariants.md), then [02-scanning-and-splicing.md](02-scanning-and-splicing.md) |
| a new selector kind, or a new option     | [06-design-decisions.md](06-design-decisions.md), [07-limitations.md](07-limitations.md)         |

## Glossary

In this section, we define words that are important to describe or understand the library. In the remainder of the documentation, we assume a common knowledge of how we understand those words in the context of this library.

| Term | Meaning |
| ---- | ------- |
| **annotation** | The HTML comment that names what to inject: `<!-- snippet: path#selector -->`. Written by the author, never rewritten by the tool. |
| **target** | What an annotation points at: a path, optionally followed by `#` and a selector. |
| **selector** | The part of a target after `#`, naming something inside the file. Absent means the whole file. |
| **region** | An annotation line together with the fenced block that opens on the next line. The unit the tool processes. |
| **fence line** | The line opening a fenced block, with its info string. Belongs to the author; see [06-design-decisions.md#the-author-owns-the-fence-line](06-design-decisions.md#the-author-owns-the-fence-line). |
| **body** | The lines between a fence line and its closing fence. The only thing the tool writes. |
| **to materialize** | To write extracted content into the Markdown file on disk, as opposed to resolving it when the document is rendered. |
| **stale** | A region whose body no longer matches what its target would produce. What `--check` reports. |

## Source map

In this section, we keep a map of the source files for easier and quicker navigation.

| Module | Owns |
| ------ | ---- |
| `__init__.py` | The public API: `process_text`, `process_file`. |
| `exceptions.py` | `SnippetError` and its subclasses. Every one carries the Markdown file and the annotation's line. |
| `_annotation.py` | Recognizing an annotation line and parsing it into an `Annotation`. |
| `_document.py` | Fence-aware scanning of a document into regions; the fence predicates. |
| `_resolve.py` | Turning a target's path into a filesystem path; finding the project root. |
| `_extract/__init__.py` | Dispatch from a selector to an extractor. The seam new selector kinds are added at. |
| `_extract/_whole.py` | Whole-file extraction. |
| `_extract/_python.py` | Python symbol lookup with `ast`: spans, decorators, dedent, ambiguity. |
| `_lang.py` | Extension to language token, used only when creating a missing fence. |
| `_text.py` | The only place bytes become text: UTF-8, LF normalization, no platform translation. |
| `_render.py` | Building a block from extracted content: fence length, right-strip, re-indent. |
| `_process.py` | The pipeline, and the one code path `--check` and rewrite both take. |
| `_cli.py` | Argument parsing, file walking, exit codes. |
