# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Finding the spans a source file marks out with comments.

A region is delimited by a ``[snippet: name]`` marker and a ``[/snippet]``
marker, each written as a comment alone on its line. The markers are recognized
as text, in any file, whatever its language.

Dev Notes:
    docs-dev/architecture/03-extraction.md#named-regions
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from markdown_code_snippet import _text
from markdown_code_snippet.exceptions import RegionMarkerError

if TYPE_CHECKING:
    from pathlib import Path

_NAME = r"[A-Za-z_][A-Za-z0-9_-]*"
_BODY = rf"\[(?P<close>/?)snippet(?::[ \t]*(?P<name>{_NAME}))?\]"

#: A marker written as a line comment in any of the common syntaxes.
_COMMENT = re.compile(rf"^[ \t]*(?:#|//|;|--)[ \t]*{_BODY}[ \t]*$")

#: A marker written as an HTML comment, which is the only one with a closer.
_HTML = re.compile(rf"^[ \t]*<!--[ \t]*{_BODY}[ \t]*-->[ \t]*$")

#: Loose enough to notice that a line *means* to be a marker, so that a
#: malformed one is reported instead of silently read as ordinary text.
_INTENT = re.compile(r"^[ \t]*(?:#|//|;|--|<!--)[ \t]*\[/?snippet\b")

#: A region still open while scanning: its name and the line it opened on.
_Open = tuple[str, int]


@dataclass(frozen=True)
class Region:
    """A named span of a source file.

    Attributes:
        name: The name the start marker gives it.
        opened: The 1-based line of the start marker.
        closed: The 1-based line of the end marker.
        body: The lines between the two markers, joined with newlines. The
            markers themselves are not part of it.
    """

    name: str
    opened: int
    closed: int
    body: str


def find_regions(path: Path) -> dict[str, Region]:
    """Return every region a source file marks out, keyed by name.

    An empty dict means the file marks nothing out.

    Raises:
        RegionMarkerError: A marker is malformed, a region is nested, reused,
            never closed, or closed without being opened.
        SourceUnreadable: The file cannot be read as UTF-8 text.
    """
    lines = _text.read(path).split("\n")
    regions: dict[str, Region] = {}
    open_: _Open | None = None

    for number, line in enumerate(lines, start=1):
        marker = _marker(line)
        if marker is None:
            if _INTENT.match(line):
                raise _malformed(path, number)
        elif marker[0]:
            region = _close(path, number, marker[1], open_, lines)
            regions[region.name] = region
            open_ = None
        else:
            open_ = _open(path, number, marker[1], open_, regions)

    if open_ is not None:
        name, opened = open_
        raise RegionMarkerError(
            path,
            opened,
            f"region {name!r} is never closed by [/snippet]",
        )
    return regions


def _marker(line: str) -> tuple[bool, str | None] | None:
    """Return ``(is_end, name)`` for a well-formed marker line, else None."""
    found = _COMMENT.match(line) or _HTML.match(line)
    if found is None:
        return None
    return found.group("close") == "/", found.group("name")


def _open(
    path: Path,
    number: int,
    name: str | None,
    open_: _Open | None,
    regions: dict[str, Region],
) -> _Open:
    """Check a start marker, and return the region it leaves open."""
    if name is None:
        raise _malformed(path, number)
    if open_ is not None:
        raise RegionMarkerError(
            path,
            number,
            f"region {name!r} starts inside region {open_[0]!r}, opened at"
            f" line {open_[1]}; regions cannot nest",
        )
    if name in regions:
        raise RegionMarkerError(
            path,
            number,
            f"region {name!r} is already defined at line"
            f" {regions[name].opened}",
        )
    return name, number


def _close(
    path: Path,
    number: int,
    name: str | None,
    open_: _Open | None,
    lines: list[str],
) -> Region:
    """Check an end marker, and return the region it closes."""
    if name is not None:
        raise _malformed(path, number)
    if open_ is None:
        raise RegionMarkerError(path, number, "[/snippet] closes no region")
    opened_name, opened = open_
    body = "\n".join(lines[opened : number - 1])
    return Region(opened_name, opened, number, body)


def _malformed(path: Path, number: int) -> RegionMarkerError:
    """Build the error for a line that means to be a marker and is not one."""
    return RegionMarkerError(
        path,
        number,
        "a region marker must be a comment alone on its line, written"
        " [snippet: name] to open and [/snippet] to close",
    )
