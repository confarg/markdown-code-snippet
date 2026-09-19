"""Example domain objects, quoted by the README and the documentation.

Nothing imports this module. It exists so that the project's own documentation
is built by the tool the project ships, which is the only way to be sure the
tool works on a real file rather than on a fixture.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ROLES: tuple[str, ...] = ("reader",)


@dataclass(frozen=True, slots=True)
class User:
    """A person who can sign in."""

    name: str
    email: str
    roles: tuple[str, ...] = DEFAULT_ROLES

    def rename(self, name: str) -> User:
        """Return a copy of this user under a new name."""
        return User(name=name, email=self.email, roles=self.roles)
