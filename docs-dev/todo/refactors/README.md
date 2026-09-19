# Refactors

Code that works but should be cleaner: duplication, misplaced modules, dead weight, test
hygiene, performance. One ticket per file; see [../README.md](../README.md) for the format.

A refactor whose impact is anything but `none` is not really a refactor — it reaches users, and
wants either a decision in
[../../architecture/06-design-decisions.md](../../architecture/06-design-decisions.md) or a
different board.

<!-- tickets:start -->

| Ticket | Effort | Risk | Impact |
|---|---|---|---|
| [REF-1 — `COM812` is selected, and ruff warns it conflicts with the formatter](REF-1-com812-conflicts-with-the-formatter.md) | S | low | none |
| [REF-2 — `docs-dev/todo/index.py` does not satisfy the project's own lint rules](REF-2-index-py-exceeds-the-line-length.md) | S | low | none |

<!-- tickets:end -->
