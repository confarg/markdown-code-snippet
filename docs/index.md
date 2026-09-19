---
icon: lucide/rocket
---

# Getting started

`markdown-code-snippet` writes code into your Markdown files, so that a snippet in the
documentation is the code that runs rather than a copy of it that used to be.

## The idea

Put a comment above a code block naming the file it should show:

````markdown
<!-- snippet: examples/config.yaml -->
```yaml
```
````

Run the tool, and the block holds the file:

<!-- snippet: ../examples/config.yaml -->
```yaml
server:
  host: localhost
  port: 8080

logging:
  level: INFO
```

That content is now **in the file on disk**. GitHub shows it, mkdocs builds it, and no plugin is
involved in either — the only thing that has to run is the tool itself, once, before you commit.

## Install it

```bash
uv add --dev markdown-code-snippet
```

Then wire it into `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/confarg/markdown-code-snippet
    rev: v0.1.0
    hooks:
      - id: markdown-code-snippet
```

The hook rewrites stale blocks and fails, so the change lands in your working tree where you can
read it. Swap in `markdown-code-snippet-check` where you want a gate that writes nothing — in CI,
for instance, to catch a commit that got in with `--no-verify`.

## Show one definition

A `#` fragment names a Python class, function, method or assignment:

<!-- snippet: ../examples/models.py#User.rename -->
```python
def rename(self, name: str) -> User:
    """Return a copy of this user under a new name."""
    return User(name=name, email=self.email, roles=self.roles)
```

A method is dedented to column zero so that it reads on its own, and a decorated definition keeps
its decorators. The file is parsed, never imported, so nothing in your repository is executed to
build your documentation.

## Keep your fence

The tool replaces the body of a block and leaves the fence line to you, which means every
mkdocs-material attribute keeps working:

````markdown
<!-- snippet: examples/config.yaml -->
```yaml title="config.yaml" hl_lines="2 3"
```
````

## Where to go next

The full annotation grammar, the path rules, the options and every error the tool can report are on
the [reference](reference.md) page.
