"""Default settings, as the documentation quotes them."""

from typing import Any, Final

DEFAULTS: Final = {
    "host": "localhost",
    "port": 8080,
}

RETRIES = 3


def configure(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the defaults with overrides applied."""
    settings = dict(DEFAULTS)
    settings.update(overrides or {})
    return settings
