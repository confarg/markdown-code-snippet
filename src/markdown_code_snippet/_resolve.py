# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Turning the path an annotation writes into a path on disk.

Dev Notes:
    docs-dev/architecture/04-paths.md
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from markdown_code_snippet.exceptions import (
    AbsolutePath,
    RootNotFound,
    TargetNotFound,
)

#: What marks a project root, nearest ancestor first. ``pyproject.toml`` marks
#: a project while ``.git`` and ``.jj`` mark a checkout that may hold several,
#: so in a monorepo the nearest match is the package the document belongs to.
ROOT_MARKERS = ("pyproject.toml", ".git", ".jj")


def find_root(start: Path) -> Path | None:
    """Return the nearest ancestor of ``start`` that marks a project root.

    ``start`` itself counts as an ancestor. Returns None when nothing above it
    is marked, which is only an error once a root-relative path is used.
    """
    for candidate in (start, *start.parents):
        if any((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate
    return None


def resolve(path: str, *, document: Path, root: Path | None) -> Path:
    """Return the file a target's path names.

    Args:
        path: The path exactly as the annotation wrote it.
        document: The Markdown file carrying the annotation.
        root: The project root, if one was found or given.

    Raises:
        AbsolutePath: The path is absolute, so it would not survive a clone.
        RootNotFound: The path is root-relative and there is no root.
        TargetNotFound: The path names nothing, or names a directory.
    """
    if path.startswith("/"):
        if root is None:
            raise RootNotFound(path)
        base, relative = root, path.lstrip("/")
    else:
        if _is_absolute(path):
            raise AbsolutePath(path)
        base, relative = document.parent, path

    resolved = (base / relative).resolve()
    if not resolved.is_file():
        raise TargetNotFound(resolved)
    return resolved


def _is_absolute(path: str) -> bool:
    """Return whether a path is absolute under either platform's rules.

    Checked for both platforms rather than the current one, so a document that
    a Windows author fixed up with ``C:/...`` is rejected on Linux too instead
    of resolving to a file nobody has.
    """
    return (
        PurePosixPath(path).is_absolute()
        or PureWindowsPath(path).is_absolute()
        or bool(PureWindowsPath(path).drive)
    )
