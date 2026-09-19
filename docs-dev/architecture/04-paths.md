# Path resolution

A snippet path is resolved against the **directory of the Markdown file that carries the
annotation**. A path beginning with `/` is resolved against the **project root** instead.

```text
docs/guide/install.md
  <!-- snippet: config.yaml -->        ->  docs/guide/config.yaml
  <!-- snippet: ../shared/a.yaml -->   ->  docs/shared/a.yaml
  <!-- snippet: /src/app.py#main -->   ->  <root>/src/app.py
```

## Why the Markdown file's directory

A snippet path sits next to relative links, relative images and relative `--8<--` includes in the
same file, and all of those are relative to the file. A path that meant something different from
its neighbors would be a trap. It also keeps a documentation subtree movable: `docs/guide/` can be
renamed without touching the annotations inside it, as long as what they point at moves with them.

The cost is that reaching source code from deep inside `docs/` would mean counting `../` segments,
which is what the `/`-prefixed form is for. Making every path root-relative instead would have
fixed that at the price of the consistency above; the trade-off is recorded in
[06-design-decisions.md#paths-are-relative-to-the-markdown-file](06-design-decisions.md#paths-are-relative-to-the-markdown-file).

The leading `/` is not an absolute filesystem path and never resolves outside the project. An
annotation cannot address anything above the root, which keeps a repository's documentation
reproducible on another machine.

## Finding the root

The root is the nearest ancestor of the Markdown file containing one of, in order:

1. `pyproject.toml`
2. `.git`
3. `.jj`

`--root DIR` overrides the search. If nothing is found and no `--root` is given, a `/`-prefixed
path is an error — a guess would silently resolve against a directory nobody chose.

`pyproject.toml` leads because it marks the project, while `.git` and `.jj` mark a *checkout* that
may hold several. The order only matters in a monorepo, where it gives the answer a reader
expects: the package the docs belong to, not the repository that contains it.

`.jj` is listed because this repository is developed with Jujutsu; a colocated checkout has both
markers, so the search finds the same directory either way.

## Resolution is one function

`_resolve.py` is the only place that turns an annotation's path into a filesystem path, and the
only place that knows about the root. Extractors receive a resolved, verified path — no extractor
ever joins a path itself, because a second joiner is how the two halves of a rule drift apart.
