<!-- snippet: /lib/models.py#User -->
```python
@dataclass(frozen=True, slots=True)
class User:
    """A person who can sign in."""

    name: str
    email: str
    roles: tuple[str, ...] = ()

    #: Every user ever constructed, newest last.
    registry: list[str] = field(default_factory=list)

    def rename(self, name: str) -> User:
        """Return a copy of this user under a new name."""
        return User(name=name, email=self.email, roles=self.roles)

    @property
    def is_admin(self) -> bool:
        """Whether this user holds the admin role."""
        return "admin" in self.roles
```
