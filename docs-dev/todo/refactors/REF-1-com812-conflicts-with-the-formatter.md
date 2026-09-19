# REF-1 — `COM812` is selected, and ruff warns it conflicts with the formatter

**Where:** `.ruff.toml`
**Filed:** 2026-09-20
**Effort:** S · **Risk:** low · **Impact:** none

`lint.select` includes `COM`, and every `ruff format` run prints:

```text
warning: The following rule may cause conflicts when used with the formatter:
`missing-trailing-comma` (`COM812`). To avoid unexpected behavior, we recommend
disabling this rule, either by removing it from the `lint.select` configuration,
or adding it to the `lint.ignore` configuration.
```

The formatter already adds the trailing commas `COM812` asks for, so the rule contributes nothing
and the warning is noise on every hook run. The fix is one line in `lint.ignore`; keeping the rest
of `COM` is still worth it (`COM818`, a trailing comma making a stray one-tuple, is a real bug
class the formatter will not catch).
