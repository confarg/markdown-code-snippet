# Annotation syntax

An annotation is an HTML comment that names a source file and, optionally, something inside it:

````markdown
<!-- snippet: examples/config.yaml -->
```yaml
host: localhost
port: 8080
```
````

The fenced block below it is **generated**: the tool owns its body and rewrites it from the
source file on every run.

## Why an HTML comment

The annotation has to survive two renderers that nobody controls. GitHub renders `README.md`
directly from the repository, and mkdocs renders the same file into a site. Markdown has exactly
one construct that both of them pass through without displaying it, and that is the HTML
comment; anything else — a directive line, a custom fence attribute, a `{% include %}` tag —
either shows up as literal text on GitHub or needs a plugin on the mkdocs side.

The alternative shape, an extension that resolves the include at render time
(`pymdownx.snippets`, `mkdocs-include-markdown-plugin`, mdBook's `{{#include}}`), was rejected
for the reason argued in
[06-design-decisions.md#materialize-rather-than-resolve-at-render-time](06-design-decisions.md#materialize-rather-than-resolve-at-render-time).

## Grammar

```text
annotation := BOL indent "<!--" ws* "snippet:" ws+ target (ws+ option)* ws* "-->" ws* EOL
target     := path ("#" selector)?
option     := key "=" value            # the value may be quoted with ' or "
```

- The annotation **starts its line**, and is **alone on it**. Two different rules, and the
  difference is what makes this document readable:
  - A comment that does not start its line is not an annotation at all. `` `<!-- snippet: a.yaml -->` ``
    in a table cell, or named in the middle of a sentence, is prose. Without this the project could
    not describe its own syntax outside a fenced block — the first draft of the README could not be
    processed for exactly that reason.
  - Text *after* the `-->` on a line that does start with an annotation **is** an error, not an
    ignored comment. A typo there must never pass silently, because the failure mode is
    documentation that quietly stops updating, and nothing distinguishes a trailing word from a
    mistake.
- The line may be **indented**. The generated block inherits that indentation, which is what
  makes a snippet work inside a list item or a mkdocs-material `=== "Tab"` block — see
  [02-scanning-and-splicing.md#indentation](02-scanning-and-splicing.md#indentation).
- `path` is resolved as described in [04-paths.md](04-paths.md).
- `selector` names something inside the file; the kinds that exist are listed in
  [03-extraction.md](03-extraction.md). No selector means the whole file.

## Options

Two, deliberately:

| Option | Default | Effect |
| ------ | ------- | ------ |
| `lang=<token>` | inferred from the file extension | The info string used **when the tool has to create a missing fence**. Ignored once a fence exists, because the fence line belongs to the author. |
| `dedent=true` / `dedent=false` | `true` | Whether the common leading indentation is removed from the extracted content. |

The list is short on purpose. Everything that decorates a code block — `title=`, `hl_lines=`,
`linenums=`, `{.no-copy}`, anything a future mkdocs-material release adds — is written on the
fence line by the author and never passes through an option here. That split is argued in
[06-design-decisions.md#the-author-owns-the-fence-line](06-design-decisions.md#the-author-owns-the-fence-line).

## Adjacency

The fence must open on the line **immediately** after the annotation: no blank line, no prose in
between. If the next line is not a fence, the tool inserts one there, with the language from
`lang=` or from the file extension.

The strictness buys a rule that fits in one sentence, and an unambiguous answer to "which block
does this annotation own?" without needing a closing marker. A blank line between an annotation
and a block is therefore not a formatting choice — it detaches them, and the tool will insert a
second block into the gap.

## Vocabulary

The terms this document introduces — annotation, target, selector, region, body — are defined in
[README.md § Glossary](README.md).
