# Limitations

Boundaries the design has, as opposed to defects it has. Each one is a consequence of a decision
in [06-design-decisions.md](06-design-decisions.md); a limitation that turns out to be unjustified
becomes a ticket on [../todo/](../todo/README.md).

## Comments above a definition are not included

A snippet of a class or function starts at its first decorator, or at its `def` or `class` line. A
comment above that line is outside the span and is left out, even when it is the explanation a
reader wants:

```python
# Kept deliberately small: the config is read once at startup.
@dataclass(frozen=True)
class Settings: ...
```

`#Settings` extracts from `@dataclass` onward. The comment is not part of the definition as far as
`ast` is concerned, and a rule for how far to walk upwards — one comment? a contiguous block?
through a blank line? — is a guess about intent. A docstring, being part of the body, is always
included, which is where an explanation meant for a reader belongs. An opt-in option is filed on
[features/](../todo/features/README.md).

## An overloaded function cannot be selected

`@overload` stubs and their implementation share a name, so a selector naming it is ambiguous and
fails by design
([06-design-decisions.md#an-ambiguous-selector-fails](06-design-decisions.md#an-ambiguous-selector-fails)).
There is no way to extract such a function today. Grouping the stubs with their implementation into
one snippet is the natural answer and is filed as a feature; until then the workaround is a whole
file, or a line range once those exist.

## Only Python has symbol selectors

`#Name` is understood in `.py` files only. In any other file a selector can name a region, and only
one the file marks out itself: showing one service out of a `docker-compose.yaml` means putting
`[snippet: …]` markers around it in that file ([03-extraction.md#named-regions](03-extraction.md#named-regions)).
Symbol extraction for other languages would need a parser per language, which is a dependency
question rather than a design one.

## Markers are recognized as text

A region marker is found by reading the file line by line, not by parsing it. The scanner does
not know that a line sits inside a Python string, a heredoc, or a block comment of another language,
so a marker-shaped line there is still a marker:

```python
HELP = """
# [snippet: usage]
"""
```

That is rare. The scanner takes a marker-shaped line as an instruction wherever it appears, so a
file that quotes its own marker syntax must not put a whole marker line in a string.

A consequence worth knowing: a marker written inside a region's own body is a nesting error, and a
marker that is never closed fails the file even for a selector that names something else in it.
That is deliberate — a file with broken markers is reported, not partly read.

## Region names cannot contain a dot

A region name follows `[A-Za-z_][A-Za-z0-9_-]*`. A dot is the selector's own separator for a
dotted path into a Python scope, so a dot is not allowed in a region's name: a marker naming
`db.primary` is reported as malformed rather than accepted and then unreachable. Choose a dash or
an underscore.

## Adjacency is strict

A blank line between an annotation and its block detaches them, and the tool inserts a new block
into the gap rather than adopting the one below
([01-annotation-syntax.md#adjacency](01-annotation-syntax.md#adjacency)). The strictness is what
removes the need for a closing marker; the cost is that a reasonable-looking edit — adding a blank
line for breathing room — changes the meaning of the document.

## Four-space indentation is not a code block

The scanner recognizes fenced code blocks only, so an annotation indented by four spaces is
processed rather than treated as literal text. This is required for mkdocs-material content tabs,
where everything is indented; the reasoning is in
[02-scanning-and-splicing.md#fence-awareness](02-scanning-and-splicing.md#fence-awareness). To show
an annotation literally, put it in a fence.

## The fence language is not checked against the file

Because the author owns the fence line, a block whose language token disagrees with the extension
of the file it draws from stays that way — a `.yaml` snippet inside a ```` ```python ```` fence is
not reported. The trade is deliberate
([06-design-decisions.md#the-author-owns-the-fence-line](06-design-decisions.md#the-author-owns-the-fence-line)),
and a `--strict` lint that flags the mismatch would fit without disturbing it.

## Root discovery has no upper bound

`find_root` walks upwards until it finds a marker, and nothing stops it at the project it
started in. On a machine whose home directory is itself a checkout — a dotfiles repository, say —
a document sitting outside any project resolves its `/`-prefixed paths against that home
directory rather than reporting that there is no root. The walk cannot tell a marker that was
meant as a project boundary from one that happens to be on the way up, and git behaves the same
way for the same reason. `--root` is the answer when it matters; the failure is loud in practice,
because the path it then looks for does not exist.

## Content is only as fresh as the last run

Materialized snippets go stale between runs by definition. `--check` is what makes staleness
detectable, and it belongs in CI as well as in pre-commit: a commit made with `--no-verify`, or a
source file changed on a branch where the docs were not touched, both produce a repository whose
documentation is wrong and whose hooks never ran.

## Only UTF-8

Source files are decoded as UTF-8; anything else is an error. Injected content also has its line
endings normalized to LF and its trailing whitespace removed
([02-scanning-and-splicing.md#whitespace](02-scanning-and-splicing.md#whitespace)), so a snippet
cannot demonstrate CRLF endings or significant trailing spaces.
