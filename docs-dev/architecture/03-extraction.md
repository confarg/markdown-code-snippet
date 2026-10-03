# Extraction

Extraction turns a target — a resolved path and an optional selector — into the text that goes
into a block body. There is one extractor per selector kind, behind a dispatch in
`_extract/__init__.py`; adding a kind means adding an extractor, never touching the scanner or the
renderer.

## Whole file

No selector means the whole file, decoded as UTF-8, with line endings normalized and trailing
blank lines dropped. Nothing else: no dedent (there is no common indentation to remove from a file
that starts at column zero), no filtering.

A file that cannot be decoded as UTF-8 is an error rather than a best-effort transcription. A
binary file in a code block is never what anyone meant.

## Python symbols

`path.py#Name` extracts the statement that defines `Name`. The lookup is **static**: the file is
parsed with `ast.parse` and the resulting node's line span is sliced out of the source text.
Nothing is imported.

Two reasons, and the first is the one that settles it:

1. A pre-commit hook must not execute the repository it is checking. Importing a module runs its
   top-level code — at commit time, on every commit, for every snippet.
2. A static parse works on files the current environment cannot import: a module with unmet
   dependencies, a file outside any package, an example that is deliberately broken to show an
   error message.

The rejected alternative is recorded in
[06-design-decisions.md#static-analysis-never-an-import](06-design-decisions.md#static-analysis-never-an-import).

### What is addressable

| Node | Reached by |
| ---- | ---------- |
| `ClassDef` | `#User` |
| `FunctionDef`, `AsyncFunctionDef` | `#load`, `#User.rename` |
| `Assign`, `AnnAssign` | `#DEFAULTS`, `#User.registry` |
| `TypeAlias` (`type X = …`) | `#Config`, `#Outer.Inner` |

A dotted selector walks scopes: `#Outer.Inner.method` descends through the body of each named
node. Only the bodies of classes and functions are descended into, so a name defined inside an
`if` or a `try` at module level is reachable by its plain name but does not create a scope.

### Decorators are part of the definition

A decorated class or function is extracted with its decorators, because the decorators are how
the documented thing behaves — a `@dataclass` shown without its decorator is a different class.

`ast` puts the `lineno` of a decorated node on its `def` or `class` line, so the span starts at
the first decorator instead. The decorator's own `lineno` is the line of the *expression* after
the `@`, which is normally the same line but need not be, so the start is walked back to the line
actually carrying the `@`. A comment between two decorators falls inside the span and is kept; a
comment above the first decorator does not and is not — see
[07-limitations.md#comments-above-a-definition-are-not-included](07-limitations.md#comments-above-a-definition-are-not-included).

### Dedent

A method sliced out of a class body carries the class body's indentation. The common leading
whitespace of the non-blank lines is removed so the snippet starts at column zero, which is what
makes it readable in isolation. `dedent=false` keeps the original columns for the rare case where
the indentation is the point.

Dedent runs before the re-indentation described in
[02-scanning-and-splicing.md#indentation](02-scanning-and-splicing.md#indentation): content is
always normalized to column zero internally, and the document's own indentation is applied once,
at render time.

### Ambiguity is an error

A selector matching more than one definition — `@overload` stubs beside their implementation, a
name defined in both branches of an `if` — raises an error naming every candidate line.

Neither silent alternative is acceptable. First-match-wins would put an overloaded function's bare
`...` stub in the documentation and nothing would ever report it. Emitting every match would quietly
concatenate definitions that have nothing to do with each other. An error costs the author one
edit and cannot mislead a reader; the argument is in
[06-design-decisions.md#an-ambiguous-selector-fails](06-design-decisions.md#an-ambiguous-selector-fails).

## Named regions

`path#name` extracts a region the file marks out itself. The file carries two marker comments,
each alone on its line:

```python
# [snippet: body]
config = load(env_prefix="MYAPP_")
# [/snippet]
```

The content between the markers is the region. It is text-level: the scanner looks for markers
in any file, whatever its language, and needs no parser. That is what lets a span start in the
middle of a function, which no symbol can name.

**The markers are not part of the output.** A region is what lies strictly between them. The
whole-file selector keeps them, because a whole file is meant to be the file.

**Comment syntaxes.** A marker is a whole-line comment in one of `#`, `//`, `;`, `--`, or an HTML
comment `<!-- -->`. The name is `[A-Za-z_][A-Za-z0-9_-]*`; the closing marker is always bare,
`[/snippet]`, and closes the region opened most recently.

**Regions do not nest, and names are unique per file.** A start marker inside an open region, a
second region with a name already used, an end marker with nothing open, and a region never
closed are all errors, each naming the line it concerns. A failed file produces no region at all,
and so no partial snippet.

**Dispatch.** A selector is first looked up among the regions of the file. For a Python file, if
no region has the name, the selector falls through to a symbol. If both answer, the selector is
an error ([06-design-decisions.md#a-region-and-a-symbol-cannot-share-a-name](06-design-decisions.md#a-region-and-a-symbol-cannot-share-a-name)).
A file with no markers and no symbol support keeps the old error.

**Dedent** applies to a region as to any extracted content: a region inside a function is read
back at column zero.

The reasons for the syntax and the stripping are in
[06-design-decisions.md#region-markers-are-comments](06-design-decisions.md#region-markers-are-comments),
and what the marker scan cannot see is in
[07-limitations.md#markers-are-recognized-as-text](07-limitations.md#markers-are-recognized-as-text).

## Errors carry a location

Every extraction failure — file missing, file undecodable, file unparsable, selector not found,
selector ambiguous, region markers unbalanced — is reported with the **Markdown file and the line number of the annotation**,
not just the source path. The reader of the error is someone who has to go and fix an annotation,
and the source file alone does not say which of them is wrong.
