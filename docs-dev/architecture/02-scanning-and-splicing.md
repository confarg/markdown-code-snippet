# Scanning and splicing

Processing a Markdown document is four steps: scan it into regions, extract each region's content
from its source file, render that content as a block body, splice the body back in. This document
covers the first and the last — the two that decide whether the result is stable.

## The region

A **region** is an annotation line plus the fenced block that opens on the next line. The
annotation line is its header, the fence line is the author's, and everything between the fence
line and its closing fence is the **body**, which the tool owns:

````markdown
<!-- snippet: config.yaml -->    <- header, never rewritten
```yaml title="config.yaml"      <- fence line, the author's
host: localhost                  <- body, generated
```                              <- closing fence
````

Splicing replaces the body and nothing else. That is what makes the operation idempotent: the two
lines that could disagree with the source file — the annotation and the fence — are inputs, not
outputs.

## Fence awareness

The scanner tracks open fences, so an annotation **inside** a fenced code block is content rather
than an annotation. Without this the project could not document its own syntax: every example
above would be processed as a real annotation the moment the tool ran over this file.

What the scanner implements is a deliberate subset of CommonMark:

- A fence opens on a line whose stripped form begins with three or more backticks or tildes, and
  closes on a later line with at least as many of the same character and nothing after them.
- **Indented code blocks (four spaces) are not recognized.** This is the one place where the
  subset matters, and it is a choice rather than an omission: content inside a mkdocs-material
  `=== "Tab"` block is indented by four spaces, and an annotation there must still work. Treating
  indentation as a code block would make tabs unusable, so an annotation that an author intended
  as literal text in an indented block is processed anyway. Put such an example in a fence.

## Indentation

The generated block is indented to match the annotation line. Extraction dedents the content to
column zero and rendering re-indents every non-empty line by the annotation's own leading
whitespace, so a snippet inside a list item or a content tab lands at the right column:

````markdown
=== "YAML"

    <!-- snippet: config.yaml -->
    ```yaml
    host: localhost
    ```
````

Blank lines stay empty rather than becoming lines of spaces, because `trailing-whitespace` would
strip them and the next run would put them back — see [Whitespace](#whitespace).

## Fence escalation

A snippet can contain a fence; including a Markdown file is the obvious case. The generated fence
therefore has to be longer than anything in the body that could close it. Only a **line-initial**
run can close a fence in CommonMark, so only those are measured: the fence is one character
longer than the longest line-initial run of its own fence character in the body, with three as
the floor.

An author's fence that is already long enough is left exactly as it is. One that is too short is
lengthened in place, with its info string preserved — lengthening is the single exception to the
author owning that line, and it exists because the alternative is emitting a broken document.
Tilde fences are escalated with tildes.

## Whitespace

Three rules, all of them about coexisting with the other hooks in a pre-commit run:

1. Every injected line is right-stripped, and trailing blank lines are dropped.
2. Line endings are normalized to LF.
3. The file ends with exactly one newline.

The first is the one that is not obvious. A source file containing a line with trailing
whitespace would be injected verbatim, `trailing-whitespace` would strip it out of the Markdown
file, and this hook would restore it on the next run: the two hooks would undo each other forever
and pre-commit would never reach a clean state. Fidelity loses to termination. The rejected
alternatives are in
[06-design-decisions.md#trailing-whitespace-is-stripped-not-preserved](06-design-decisions.md#trailing-whitespace-is-stripped-not-preserved).

## Idempotency

The property the pre-commit hook rests on is `process(process(text)) == process(text)`, and it
holds by construction rather than by accident: a region's output is a function of its annotation,
its fence line and its source file, and splicing rewrites none of those three. The test suite
still asserts it for every smoke case, because "by construction" is a claim about code that gets
edited.
