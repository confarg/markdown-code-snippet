The comment above the attribute is not part of the definition:

<!-- snippet: ../lib/models.py#User.registry -->
```python
registry: list[str] = field(default_factory=list)
```
