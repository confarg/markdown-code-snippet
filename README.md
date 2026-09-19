# markdown-code-snippet

> Inject snippets of files or Python code into Markdown files.

## Install

In your `.pre-commit-hooks.yaml`:

```yaml
repos:
  - repo: https://github.com/confarg/markdown-code-snippet
    rev: v0.0.1.dev1
    hooks:
      - id: markdown-code-snippet
```

You can also install it as a project dependency:

```bash
uv add --dev markdown-code-snippet
```

```yaml
repos:
  - repo: local
    hooks:
      - id: markdown-code-snippet
        entry: uv run markdown-code-snippet
        language: system
```

## Inject code snippets into Markdown

The tool works by reading instructions provided in HTML comments placed before a code block. The content of the code block will be overwritten during each pre-commit run.

To include a whole file:

````markdown
<!-- snippet: path/to/config.yaml -->

```yaml
db:
  port: 5432
```
````

To include a specific class:

````markdown
<!-- snippet: path/to/foo.py#Foo -->

```python
@dataclass
class Foo:
  id: int
```
````

Note that class decorators, if any, are included in the snippet.

To include a specific method:

````markdown
<!-- snippet: path/to/bar.py#Bar.get_value -->

```python
def get_value(self):
    return self.value
```
````

Note that code snippets are dedented by default. Add `dedent=false` to the info string to disable it.

To include a specific top-level definition or assignment:

````markdown
<!-- snippet: path/to/baz.py#BAZ -->

```python
BAZ: int = 42
```
````

## Paths

Relative paths are relative to the Markdown file that carries the annotation. A leading `/`
means the project root: the nearest directory above with a `pyproject.toml`, `.git`, or `.jj`,
or whatever directory `--root` names:

```text
# docs/guide/install.md
<!-- snippet: config.yaml -->        ->  docs/guide/config.yaml
<!-- snippet: ../shared/a.yaml -->   ->  docs/shared/a.yaml
<!-- snippet: /src/app.py#main -->   ->  <project root>/src/app.py
```

## Why this tool?

I was looking for a tool that copies parts of my code into my Markdown files, so that documentation always stays up-to-date. I wanted the committed Markdown to be functional, so that browsing GitHub would provide all the information and, at the same time, be usable by MkDocs or Zensical. Therefore I needed a tool where:

- the copy of code snippets happens during pre-commit;
- the copy instructions are invisible during Markdown rendering;
- the info string (the text after the opening code fence) stays in the hands of the user, e.g. to add `title:` information.
