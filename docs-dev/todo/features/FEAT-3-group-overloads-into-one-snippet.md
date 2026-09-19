# FEAT-3 — Extract an overloaded function as one snippet

**Where:** `src/markdown_code_snippet/_extract/_python.py`
**Filed:** 2026-09-20
**Effort:** S · **Risk:** low · **Impact:** behavior

`@overload` stubs share a name with their implementation, so a selector naming one is ambiguous and
fails. There is currently no way at all to extract such a function, which is a gap precisely where
the documentation is most worth generating — a typed public API
([07-limitations.md#an-overloaded-function-cannot-be-selected](../../architecture/07-limitations.md#an-overloaded-function-cannot-be-selected)).

Direction: when *every* match is a function of the same name and all but the last carry
`@overload`, the matches are one definition and the span runs from the first to the last. Anything
else stays ambiguous, so the rule in
[06-design-decisions.md#an-ambiguous-selector-fails](../../architecture/06-design-decisions.md#an-ambiguous-selector-fails)
is narrowed rather than abandoned.

Watch for: an alias in the decorator (`@typing.overload`, `@t.overload`), and stubs separated from
the implementation by other statements — those should probably stay an error.
