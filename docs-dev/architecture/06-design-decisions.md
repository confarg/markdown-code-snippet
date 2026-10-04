# Design decisions

Choices that were made deliberately, with what was rejected and why. A decision recorded here is
not re-litigated without a reason the entry does not already answer.

## Materialize rather than resolve at render time

**Decided:** the tool writes the extracted content into the Markdown file on disk.

The whole point is a file that is correct in two places at once. GitHub renders the repository's
Markdown directly and runs no plugins; mkdocs renders the same files through its own pipeline. Only
a file that already contains the code satisfies both.

Rejected: a render-time include — `pymdownx.snippets` (`--8<-- "file.py"`),
`mkdocs-include-markdown-plugin`, mdBook's `{{#include}}`, Sphinx's `literalinclude`. All of them
solve the site half and leave GitHub showing an empty code block or a literal directive. A mkdocs
plugin would also have to be installed by anyone building the docs, whereas materialized content
needs nothing on the reader's side.

The cost is a synchronization step, which is why the primary interface is a pre-commit hook with a
`--check` mode rather than a library call: the content is only as fresh as the last run, so
staleness has to be detectable by CI.

## Comment plus fence, with no closing marker

**Decided:** the annotation comment is followed immediately by a fenced block, and the closing
fence ends the generated region.

One extra line per snippet, the file is valid Markdown before the tool has ever run, and the
author keeps the fence line. `embedme` and `MarkdownSnippets` — the two existing tools that
materialize the way this one does — both landed here.

Rejected: a closing comment (`<!-- /snippet -->`), the shape `doctoc` and `cog` use. It is more
robust in one specific way — a human deleting the closing fence cannot make the tool swallow the
rest of the document — and it would leave room to generate more than a single block later
(content tabs, a `<details>` wrapper, raw Markdown). It costs two to three lines of visible source
noise per snippet, forever, for a failure mode that already leaves the document broken in an
obvious way. If generating a multi-block region is ever wanted, an opt-in closing marker can be
added without changing what is specified today.

Rejected: accepting both forms. Two terminator rules, two sets of corner cases, and a
specification that has to explain when each applies.

## The author owns the fence line

**Decided:** the tool rewrites the block body. It writes the fence line only when it has to create
a missing fence, and afterwards touches it only to lengthen a fence the body would close.

mkdocs-material alone puts `title=`, `linenums=`, `hl_lines=`, `{.no-copy}` and more on that line,
and it keeps adding to the list. Proxying each of them through a tool-side option is a race the
tool cannot win: every attribute it has not implemented is an attribute a user cannot write.
Leaving the line alone means the tool never needs to know any of them exist, and a new
mkdocs-material feature works the day it ships.

Rejected: the annotation owning the whole region, fence line included. It makes idempotency
trivially provable and keeps the language token honest against the source extension, but it caps
the block's expressiveness at whatever options the tool implements.

Rejected: split ownership — the tool rewriting the leading language token and preserving the rest.
It keeps the language in step with the file extension, which is a genuine benefit, but it requires
specifying what counts as the language token across `attr_list`, brace-attribute and bare-word
info-string styles, and it rewrites a line the author wrote.

The consequence to accept: `lang=` is only consulted when creating a fence, and a fence whose
language does not match its source file stays wrong until someone fixes it by hand.

## Only a line-initial comment is an annotation

**Decided:** a `<!-- snippet: … -->` comment is an annotation only when it starts its line, after
optional indentation. One that does not is prose. One that does, but carries text after its `-->`,
is an error.

The first shape of this rule treated *any* line containing the comment as meaning to be an
annotation, so that a typo could not pass as prose. It was written before the README was, and the
README could not be processed: its own tables name annotations in code spans, cell by cell, and
every one of them was reported as malformed. Making the syntax undocumentable outside a fenced
block is too high a price for catching a mistake nobody has made.

What survives is the half that catches something real. `<!-- snippet: a.yaml --> and then prose`
has committed to being an annotation and then gone wrong; there is no reading of it that is
deliberate. A mid-sentence mention, on the other hand, is almost always someone writing *about* the
tool, which is why the intent check is anchored to the start of the line.

Rejected: a distinct spelling for a quoted annotation, an escape such as `<!-- \snippet: … -->`.
It would restore the strict check, at the cost of a second syntax to learn whose only purpose is to
talk about the first.

## The target is a path with a fragment

**Decided:** `path#selector`, with options as trailing `key=value` pairs.

It mirrors a GitHub anchor, so `src/models.py#User` reads as "this location inside this file"
without explanation, and the dominant case — a whole file — stays a bare path.

Rejected: naming every part (`path="…" object="…"`), which is uniform but verbose exactly where
brevity matters most. Rejected: an inline YAML mapping, which is the most extensible and the least
readable, and would add a YAML parser to a library whose dependency list is otherwise empty.

Rejected: a dotted import path, `mkdocstrings`-style (`::: pkg.mod.User`). It addresses an object
rather than a file, which requires an import to resolve and cannot point at a file that is not in
a package — see the next entry.

## Static analysis, never an import

**Decided:** Python symbols are located with `ast.parse` and sliced out of the source text.

A pre-commit hook runs on every commit. Importing a module to inspect it runs that module's
top-level code, which means a commit can have side effects, and it makes extraction depend on the
hook's environment being able to satisfy the target's imports. Static parsing has neither problem
and works on files that are not importable at all. Sphinx's `:pyobject:` and `griffe`, behind
`mkdocstrings-python`, both default to static analysis for the same reasons.

Rejected: `importlib` plus `inspect.getsource`. It follows re-exports and sees dynamically created
objects, neither of which is worth executing a repository for. Rejected: static by default with an
opt-in import, which doubles the resolution paths and the error surface to serve a case nobody has
asked for yet. If it is ever needed, it arrives as an option and a second extractor.

## An ambiguous selector fails

**Decided:** a selector matching more than one definition raises an error listing every candidate
line.

`@overload` makes this common in typed code, and both silent answers are worse than an error.
First-match-wins would put a bare `...` stub in the documentation, which looks like a rendering bug
and would never be reported. Emitting every match would concatenate a name's unrelated definitions
from two branches of an `if` into one confusing block.

The consequence to accept: an overloaded function cannot currently be extracted at all. That is
filed as a feature rather than papered over —
[07-limitations.md#an-overloaded-function-cannot-be-selected](07-limitations.md#an-overloaded-function-cannot-be-selected).

## Paths are relative to the Markdown file

**Decided:** relative to the containing file's directory, with a leading `/` meaning the project
root.

Argued in [04-paths.md#why-the-markdown-files-directory](04-paths.md#why-the-markdown-files-directory).

Rejected: root-relative everywhere, which survives moving a Markdown file but makes snippet paths
disagree with every relative link beside them. Rejected: relative-only with no root form, which is
the simplest rule to state and pays for it in `../../../` chains from deep inside `docs/`.

## Trailing whitespace is stripped, not preserved

**Decided:** every injected line is right-stripped and trailing blank lines are dropped.

This tool shares a pre-commit run with `trailing-whitespace` and `end-of-file-fixer`. Injecting a
source line that ends in spaces means `trailing-whitespace` strips it and this hook restores it,
forever: the run never converges and no commit ever succeeds. A hook that cannot terminate is not
a hook.

Rejected: verbatim injection, which is more faithful and non-terminating in exactly the case above.
Rejected: verbatim plus an error when the extracted content has trailing whitespace, which is loud
and correct but fails on source files the documentation author may not control, for a difference
no reader can see.

## No configuration file in v1

**Decided:** `--root` is the only knob, passed on the command line.

pre-commit passes arguments to hooks, so a flag is enough for the one setting that exists, and a
config file would need a discovery rule, a precedence rule against the flag, and a schema — three
decisions in service of nothing yet. A `[tool.markdown-code-snippet]` table is filed on
[features/](../todo/features/README.md) for when a second setting exists.

## Whole files and Python symbols only

**Decided for v1:** the tool extracts an entire file, or one Python definition by name.

Named regions were added afterwards, behind the extractor dispatch, and are argued in the entries
below. GitHub-style line ranges remain a feature. They are the one selector kind that is silently
wrong after an unrelated edit above the range, which is a reason to think before adding them rather
than to add them first.

## Region markers are comments

**Decided:** a region is delimited by `[snippet: name]` and `[/snippet]`, each written as a comment
alone on its line. The comment syntaxes recognized are `#`, `//`, `;`, `--`, and `<!-- -->`.

The marker has to live in the source file, in whatever language it is, so the choice of carrier is
the choice of a comment. A comment is the only thing every language already has and that a
formatter, a linter and a reader all treat as inert. The spelling follows the annotation's own
`snippet:` vocabulary, so the author has one word to learn for both sides of the tool.

Precedent: `pymdownx.snippets` delimits sections with `--8<-- [start:name]` and `[end:name]` inside
a comment, in any file, and removes them from the output. C# and VS Code read `#region` /
`#endregion` pairs out of ordinary comments in the same way. The closer here is bare, not
`[/snippet: name]` as `pymdownx.snippets` writes it, because regions cannot nest: the scanner always
knows which region a closer belongs to, so the name would only be a second place to mistype.

Rejected: a closing marker that repeats the name, `[/snippet: name]`. A mismatched closer would be
caught by the name check, but that is a rule the bare closer does not need.

Rejected: a sentinel that is not a comment, such as a line of `=====`. Every language would need its
own, none of them would be inert to a formatter, and none would be recognizable to a reader.

## Region markers are stripped from the output

**Decided:** the marker lines are not part of a region's content. A region is what lies between
them, and the whole-file selector keeps them.

A marker is an instruction to the tool, not part of the code it brackets. Leaving it in would
show `# [snippet: body]` to a reader of the documentation, and a reader cannot act on it. The
whole-file selector keeps them because a whole file is, by definition, the file.

Precedent: `pymdownx.snippets` removes its section markers from included text.

## Regions do not nest

**Decided:** a region may not start while another is open, and a name may be used once per file.

Nesting would let an outer region contain inner markers that would then have to be stripped from
its content, which is a second rule about which lines count. With flat regions every line belongs to
at most one region, and any output is a single unambiguous span. A duplicate name is the same
ambiguity in another form, and is an error for the same reason a duplicate symbol is
([an ambiguous selector fails](#an-ambiguous-selector-fails)).

Rejected: allowing nesting and selecting the innermost, or every level. The first hides the outer
span from a reader; the second is the concatenation problem that ambiguity already rules out.

## A region and a symbol cannot share a name

**Decided:** in a Python file, a selector that names both a region and a definition is an error,
and neither silently wins.

A Python file can be addressed both by a `#Name` symbol and by a marked region, so the same selector
has two meanings. Letting the region win would silently change what an existing `#load` selector
shows the day someone adds a `[snippet: load]` marker, which is exactly the silent change the
ambiguity rule exists to prevent. Letting the symbol win would make a region useless in any file
that also has a definition of the same name. The error costs the author one rename, and the message
names both lines.

A file with a region and a broken Python syntax is not an error. A file that does not parse defines
no symbol, so there is nothing for the region to clash with.
