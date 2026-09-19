# Boards

Open work on this library, split into four boards. They are the standing place for
**drive-by findings**: anything you notice while doing something else and must not
silently fix, forget, or fold into an unrelated change.

| Board                             | Holds                                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [bugs/](bugs/README.md)           | Things that are wrong: defects, parity gaps, code that deviates from the documented intent.                  |
| [features/](features/README.md)   | Things that are missing: desirable behavior, and unvetted ideas worth considering.                           |
| [refactors/](refactors/README.md) | Things that work but should be cleaner: duplication, misplaced code, dead weight, test hygiene, performance. |
| [questions/](questions/README.md) | Things only the maintainer can settle: missing rationale, undecided trade-offs.                              |

The boards say _what is left to do_. `../architecture/` says _why the code is the way
it is_. A closed ticket often leaves a decision behind — the decision goes to
`../architecture/`, not here.
Boards hold open work only: a ticket's file is deleted when it closes, and its ID is named in
the revision that closed it.

## One ticket, one file

Every ticket is its own file inside its board's folder, named `<ID>-<slug>.md`:
`bugs/BUG-3-tilde-fence-not-lengthened.md`. The ID leads, because that is what code comments and
revision descriptions cite; the slug only makes a directory listing readable and may be
reworded freely. The file opens with `# <ID> — <headline>` and holds nothing else.

Each board folder also carries a `README.md`: the board's intro, and a table of its open
tickets with effort, risk and impact. **The ticket files are authoritative and the table is a
view of them**, so the table is generated, never edited. After filing, closing or re-sizing a
ticket, run:

```bash
uv run python docs-dev/todo/index.py
```

It rewrites the table between the `tickets:start` and `tickets:end` markers, leaving the prose
around them alone, and checks what it reads on the way past: a filename that disagrees with its
heading, a board holding another board's prefix, a missing or misspelled effort, risk or
impact, a bug ticket with no reproduction, and two tickets claiming one ID. `--check` writes
nothing and exits non-zero instead, which is the form for CI.

Documentation defects go on these same boards, sorted the same way: documentation wrong about
itself is a bug, documentation that is missing is a feature, documentation merely untidy is a
refactor. There is no separate documentation board, because the boards sort by _what the entry
is_ and not by which files it touches — and `**Where:**` already says which files those are.

## Ticket format

````markdown
# BUG-99 — One-line summary in the imperative or as a defect statement

**Where:** `src/markdown_code_snippet/_render.py` · **Filed:** 2026-09-20 · _(inferred — from code
reading, no test covers it)_
**Effort:** M · **Risk:** high · **Impact:** config

Two or three lines: what is wrong, when it bites, and what the fix direction looks like.
Link the rationale it touches:
[02-scanning-and-splicing.md#fence-escalation](../../architecture/02-scanning-and-splicing.md#fence-escalation).

```python
from pathlib import Path

from markdown_code_snippet import process_text

Path("inner.md").write_text("~~~bash\nrun\n~~~\n")
document = "<!-- snippet: inner.md -->\n~~~markdown\n~~~\n"

print(process_text(document, document=Path("doc.md")))
# expected: the fence lengthened to ~~~~, enclosing the body
# actual:   still ~~~markdown, so the body's own ~~~ closes the block early
```
````

- **ID**: prefix (`BUG` / `FEAT` / `REF` / `Q`) plus the next unused number on that board.
  IDs are never reused, so they stay greppable in code comments and revision descriptions.
  Read the board folder to find the next number; neither the table nor your memory is
  authoritative, and a duplicate ID is easy to create and hard to notice afterwards.
- **Confidence**: mark anything you have not actually observed as _(inferred)_, as in the
  architecture notes. A suspicion is worth filing; a suspicion sold as a fact is not.
- **Reproduction**: every ticket on `bugs/` ends with one. See [Reproduction](#reproduction).
  The other three boards are exempt — nothing is broken yet to reproduce.
- **Effort, risk and impact**: every ticket on `bugs/`, `features/` and `refactors/` carries
  all three, on their own line under `**Where:**`. See [Effort](#effort), [Risk](#risk) and
  [Impact](#impact). `questions/` is exempt — a question is answered, not implemented.
- **Ordering**: tickets sort by ID, which is filing order, so the newest is last. There is no
  priority field — say it in the body if it matters.
- **Links** are relative to the ticket file, which sits one level deeper than the board:
  `../../architecture/…`.
- Keep it short. The code and `../architecture/` hold the detail; a ticket only has to be
  enough to pick the work up cold.

## Reproduction

A bug ticket is not filed until someone else can see the bug for themselves. Every entry on
`bugs/` therefore ends with a **reproduction**: the smallest thing someone can run that shows
the defect, with the expected outcome and the actual one side by side.

For a defect in the code, that is a **runnable snippet**:

- **Runnable as written.** A `.py` file someone can paste into a scratch directory and run,
  using `markdown_code_snippet` and the standard library and nothing else. No pytest, no
  fixtures, no repository test helpers: a ticket is read cold, often by someone who has not
  cloned anything yet. A bug that needs a source file and a document to show itself needs both;
  write each one out in the snippet rather than assuming it is there.
- **Smallest shape that still shows it.** One annotation where one is enough, one line of source
  where the content does not matter, `document=` passed explicitly, and the document's text as a
  literal rather than read from a file the reader does not have. A bug in the command line is
  shown through `main([...])` or a `console` block, not through a hand-built `argv`.

For a defect in the documentation itself there is no program to run, so the reproduction is the
**broken reference and what it fails to reach**: a `console` block showing the command that
finds it — a `grep`, a link check — and the target it lands on instead.

Everything below applies to both kinds.

- **Expected against actual, both spelled out.** Either as trailing comments, as above, or as
  two labelled blocks when the difference is a document the tool wrote. Say which one is which;
  a reader must never have to work out which line is the bug.
- **Copied from a real run, not predicted.** Paste the actual exception type and message the
  snippet produced, or the actual bytes the tool wrote. If you cannot run it — a platform you
  are not on, a `.gitignore`d file you do not have — keep the _(inferred)_ marker and label the
  actual line as predicted, in those words. Never let a guessed transcript read like a
  transcript.
- **Running it settles the confidence marker.** If an _(inferred)_ ticket reproduces, drop the
  marker in the same edit. If it does not reproduce, the ticket is wrong: correct the entry or
  delete it — do not leave a reproduction on the board that nobody can make fail.
- **The reproduction is not the regression test.** It stays on the board, never in `tests/`.
  Fixing the bug starts by turning it into a real test under the test-first protocol, and
  closing the ticket deletes the file it lives in.

## Effort

How much work the change is, anchored to properties of this repository rather than to hours,
which nobody can predict and which age badly:

|      |                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------- |
| `S`  | One module, mechanical. The design is obvious and the existing tests already cover the behavior.                                       |
| `M`  | A few modules, or one new selector kind behind the extractor dispatch. The design is settled; the work is writing it and its tests.    |
| `L`  | Crosses the scanner, the extractors and the renderer, **or** needs a new decision recorded in `../architecture/`, **or** sweeps the whole test suite. |
| `XL` | A new subsystem or a new public seam, with several design axes still open.                                                              |

An unvetted idea has no design yet, so its implementation cannot honestly be sized. Size the
**design pass** instead — deciding whether to do it at all is the next actionable step — and
say so: `**Effort:** M *(design pass; implementation not sized)*`. Size that pass by the
investigation it needs, not by the `L` clause above: a design pass always ends in a decision
record, so reading that clause literally would make every one of them `L`.

## Risk

**What catches the mistake if the change turns out to be wrong** — not how likely that is, and
not how much work it is. Read it as: how loudly does this repository fail when you get it
wrong?

|          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `low`    | An existing test fails. The suite catches you before you commit.                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `medium` | Nothing covers it yet, and a mistake stays silent in **one** situation while the rest stays correct — only a created fence, only a tilde fence, only a document with no final newline. Closing it means adding a case that exercises that situation.                                                                                                                                                             |
| `high`   | Nothing covers it yet, and a mistake is silent **everywhere at once** — the scanner, the splicer, the whitespace rules, idempotency, anything under [05-invariants.md](../architecture/05-invariants.md), the [fragile couplings](../architecture/05-invariants.md#fragile-couplings) above all. Closing it means extending the smoke corpus, because that is what asserts a document end to end. |

Risk and effort are independent: FEAT-2 is a small addition behind the extractor dispatch that
nothing yet covers (`S`, medium), while a wide mechanical move of test files that the suite
catches instantly is `M`, low.

Do **not** score by how careful you intend to be, or by how small the edit looks. Two tickets
in the same module can differ honestly: a one-line change to a branch nothing exercises is
`high`, while a much larger edit to a fully covered function is `low`.

## Impact

**What a user of the library has to change**, assuming the change is _correct_. Risk is about
us catching a mistake; impact is about them feeling a success. The two are independent, and
the rungs run in order of how late the user finds out:

|            |                                                                                                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `none`     | Invisible to a user of the library. Internal structure, tests, internal documentation. Nothing anyone writes or runs changes.                                             |
| `behavior` | A user sees a difference but changes nothing: a new flag or field shape becomes available, an error message improves, something that used to fail starts working.         |
| `api`      | A user's **code** must change — a public signature, keyword name, import path or exception type. It fails loudly, at import or under a type checker, at development time. |
| `config`   | A user's **annotations or invocation** must change — an annotation that works today stops working, or starts meaning something else, or a command-line flag changes what it does. |

Where a change is both, take the higher rung. `config` outranks `api` deliberately: an API
break is caught by the tools a user already runs, while an annotation break passes every one of
them. The case to keep in mind is a change to what a selector resolves to, or to the base a
`/`-prefixed path resolves against: every existing annotation still parses, the hook still exits
zero, and the documentation now shows the wrong code — or the right code from the wrong file —
with nothing anywhere reporting it.

Impact doubles as a smell test on a refactor: anything above `none` on `refactors/` is not
really a refactor. A ticket that renames a public function is `api`, which is what says it needs
a deprecation story rather than a rename.
