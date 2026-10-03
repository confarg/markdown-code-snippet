---
icon: lucide/book-open-text
---

# Reference

## The annotation

```text
<!-- snippet: <path>[#<selector>] [key=value ...] -->
```

It must **start its line**, with nothing before it but indentation, and the fenced block it fills
must open on the **very next line**. If no fence is there, the tool writes one.

A mention of the syntax that does not start its line — in a table cell, in a code span, in the
middle of a sentence — is ordinary prose, which is how this page can describe the syntax at all.
Text *after* the `-->` on an annotation's own line is an error, because it is far more likely to be
a mistake than a decision.

An annotation inside a fenced code block is content too. To show one literally, put it in a fence
one backtick longer than the block it contains.

## Selectors

| Target | Extracts |
| ------ | -------- |
| `path/to/file.yaml` | the whole file |
| `path/to/module.py#Name` | a class, function or assignment named `Name` |
| `path/to/module.py#Class.method` | a method, dedented to column zero |
| `path/to/module.py#Outer.Inner.method` | any depth of nesting |
| `path/to/config.yaml#name` | the region the file marks out as `name` |

Decorators are part of a definition and come with it. A docstring is part of the body and comes
with it. A comment *above* the definition does not.

Only `.py` and `.pyi` files have symbol selectors. A selector on any other file is an error rather
than a silently ignored fragment, unless the file marks out a region of that name.

## Named regions

A file can mark out a span itself, with two comments each alone on its line:

```python
# [snippet: body]
config = load(env_prefix="MYAPP_")
# [/snippet]
```

`path#body` extracts what lies between the markers, and the markers are not part of the output.
The comment can be `#`, `//`, `;`, `--`, or an HTML comment `<!-- [snippet: body] -->`. The name is
letters, digits, `_` and `-`, and the closing marker is always `[/snippet]`.

Because it is a comment, the marker works in any language and survives a formatter that keeps
comments on their own line. It also reaches inside a function, where no symbol can. A region is
dedented like any other extracted content.

Regions cannot nest, and a name can be used once per file. A file whose markers do not balance is
an error that names the line, and so is a name that is both a region and a Python definition, since
the tool will not guess which one you meant.

A selector matching more than one definition — `@overload` stubs beside their implementation, a
name assigned twice — is an error listing every line it matched. The tool does not choose for you.

## Options

| Option | Default | Effect |
| ------ | ------- | ------ |
| `lang=<token>` | guessed from the file name | The info string for a fence the tool has to create. Ignored once a fence exists. |
| `dedent=false` | `dedent=true` | Keep the extracted content's own indentation instead of normalizing it to column zero. |

Values may be quoted: `lang="text linenums=1"`. An unknown option is an error — everything else
that decorates a code block goes on the fence line, which the tool does not touch.

## Paths

Relative to the directory of the Markdown file. A leading `/` is relative to the project root: the
nearest directory at or above the document holding a `pyproject.toml`, a `.git` or a `.jj`, unless
`--root` names one.

An absolute path, with a drive letter or a UNC prefix, is refused: it could not survive a clone.

## The command line

```text
markdown-code-snippet [--check] [--root DIR] PATH [PATH ...]
```

A `PATH` is a Markdown file, or a directory to search for `*.md`.

| Exit code | Meaning |
| --------- | ------- |
| `0` | Nothing to do. Every snippet was already current. |
| `1` | A file was rewritten, or with `--check`, is out of date. |
| `2` | An annotation could not be resolved. Nothing was written for that file. |

`--check` writes nothing and takes every other step, so it can never pass on a file that a rewrite
would change.

## Guarantees

- Running the tool twice changes nothing the second time.
- A document containing no annotation is not written at all.
- Injected lines carry no trailing whitespace, line endings are LF, and a document the tool writes
  ends in exactly one newline — so `trailing-whitespace`, `mixed-line-ending` and
  `end-of-file-fixer` have nothing left to change.
- A document is only written once every one of its snippets has been extracted, so a failure never
  leaves half a document updated.

## Errors

Every message names the Markdown file and the line of the annotation that caused it.

| Error | Means |
| ----- | ----- |
| `AnnotationError` | The annotation itself is malformed: no file named, an unknown option, text after the `-->`. |
| `UnclosedBlock` | The block below an annotation has no closing fence. |
| `TargetNotFound` | The path names nothing, or names a directory. |
| `SourceUnreadable` | The file cannot be read, or is not valid UTF-8. |
| `SourceUnparsable` | A Python file will not parse. |
| `AbsolutePath` | The path has a drive letter or a UNC prefix. |
| `RootNotFound` | A `/`-prefixed path was used and no root could be found. |
| `SelectorUnsupported` | A selector was given for a file that has no symbols and marks out no regions. |
| `SelectorNotFound` | The file defines no such name. The message lists what it does define. |
| `SelectorNotAScope` | A dotted selector tried to descend into a value. |
| `AmbiguousSelector` | The name is defined more than once. The message lists the lines. |
| `SelectorNamesTwice` | The name is both a region and a Python definition. The message gives both lines. |
| `RegionMarkerError` | A region marker is malformed, nested, reused, unclosed, or closes nothing. The message gives the line. |

All of them subclass `SnippetError`.

## The Python API

```python
from pathlib import Path

from markdown_code_snippet import check_file, process_file, process_text

process_file(Path("README.md"))  # rewrite; True if it wrote
check_file(Path("README.md"))  # True if stale; writes nothing
process_text(text, document=Path("a.md"))  # pure; returns the new text
```

`process_text` takes the document's path because paths resolve against it and errors are reported
against it, not because it reads it.
