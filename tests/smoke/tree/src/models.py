"""Domain objects the documentation examples quote."""

from __future__ import annotations

from dataclasses import dataclass, field


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


class Team:
    """A named group of users."""

    class Invite:
        """A pending invitation to a team."""

        def accept(self) -> None:
            """Turn the invitation into a membership."""

    def add(self, user: User) -> None:
        """Add a user to the team."""
