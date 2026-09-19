<!-- snippet: ../lib/settings.py#configure -->
```python
def configure(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the defaults with overrides applied."""
    settings = dict(DEFAULTS)
    settings.update(overrides or {})
    return settings
```
