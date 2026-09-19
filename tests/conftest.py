# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Fixtures shared by the unit tests.

The smoke corpus has its own fixtures in ``tests/smoke/``: it works from files
committed to the repository, while the tests here write the small, deliberately
odd files each of them needs.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def write(tmp_path: Path):
    """Return a helper writing a file under the temporary directory.

    The text is dedented and its leading newline dropped, so a fixture can be
    written as an indented triple-quoted string and still start at column zero.
    Bytes are written directly: text mode would translate line endings on
    Windows and the tests assert on exact output.
    """

    def _write(name: str, text: str) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(textwrap.dedent(text).lstrip("\n").encode("utf-8"))
        return path

    return _write


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Mark the temporary directory as a project root and return it."""
    (tmp_path / "pyproject.toml").write_bytes(b"")
    return tmp_path
