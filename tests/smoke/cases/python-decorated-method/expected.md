<!-- snippet: ../src/models.py#User.is_admin -->
```python
@property
def is_admin(self) -> bool:
    """Whether this user holds the admin role."""
    return "admin" in self.roles
```
