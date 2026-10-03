<!-- snippet: ../src/models.py#User.rename dedent=false -->
```python
    def rename(self, name: str) -> User:
        """Return a copy of this user under a new name."""
        return User(name=name, email=self.email, roles=self.roles)
```
