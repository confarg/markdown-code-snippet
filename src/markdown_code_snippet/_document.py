# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Scanning a Markdown document into the regions the tool owns.

Dev Notes:
    docs-dev/architecture/02-scanning-and-splicing.md#fence-awareness
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from markdown_code_snippet._annotation import (
    Annotation,
    looks_like_annotation,
    parse,
)
from markdown_code_snippet.exceptions import UnclosedBlock

_FENCE = re.compile(r"^(?P<indent>[ \t]*)(?P<run>`{3,}|~{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class Fence:
    """An opening fence line, taken apart.

    Attributes:
        indent: The leading whitespace, kept when the line is rewritten.
        char: The fence character, a backtick or a tilde.
        length: How many fence characters the line carries.
        info: Everything after them, the author's to keep.
    """

    indent: str
    char: str
    length: int
    info: str

    @property
    def line(self) -> str:
        """Return the fence line as it should be written."""
        return f"{self.indent}{self.char * self.length}{self.info}"


@dataclass(frozen=True)
class Region:
    """An annotation and the span of lines the tool replaces for it.

    ``start`` and ``stop`` bracket everything after the annotation line that
    belongs to the generated block: the opening fence, the body, and the
    closing fence. They are equal when the annotation has no block yet, which
    is how an insertion is expressed.

    Attributes:
        annotation: The parsed annotation line.
        fence: The existing opening fence, or None if there is no block.
        start: Index of the first line to replace.
        stop: Index after the last line to replace.
    """

    annotation: Annotation
    fence: Fence | None
    start: int
    stop: int


def match_fence(line: str) -> Fence | None:
    """Return the fence this line opens, or None if it opens none."""
    found = _FENCE.match(line)
    if found is None:
        return None
    run = found.group("run")
    return Fence(
        indent=found.group("indent"),
        char=run[0],
        length=len(run),
        info=found.group("info"),
    )


def closes(fence: Fence, line: str) -> bool:
    """Return whether this line closes the given fence.

    A closing fence uses the same character, is at least as long, and carries
    nothing else.
    """
    found = match_fence(line)
    return (
        found is not None
        and found.char == fence.char
        and found.length >= fence.length
        and not found.info.strip()
    )


def scan(lines: list[str]) -> list[Region]:
    """Return the regions of a document, in the order they appear.

    Fenced blocks that no annotation introduces are skipped whole, so an
    annotation quoted inside one is content rather than an annotation.

    Raises:
        AnnotationError: A line means to be an annotation but is malformed.
        UnclosedBlock: A region's block runs off the end of the document.
    """
    regions: list[Region] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if looks_like_annotation(line):
            region = _region(lines, index)
            regions.append(region)
            index = region.stop
            continue
        fence = match_fence(line)
        if fence is not None:
            index = _end_of_block(lines, index, fence)
            continue
        index += 1
    return regions


def _region(lines: list[str], index: int) -> Region:
    """Build the region introduced by the annotation at ``index``."""
    annotation = parse(lines[index], index + 1)
    start = index + 1
    fence = match_fence(lines[start]) if start < len(lines) else None
    if fence is None:
        return Region(annotation, None, start, start)

    stop = _end_of_block(lines, start, fence)
    if stop > len(lines):
        raise UnclosedBlock().located(annotation.line)
    return Region(annotation, fence, start, stop)


def _end_of_block(lines: list[str], index: int, fence: Fence) -> int:
    """Return the index after the fence closing the block opened at ``index``.

    An unclosed block yields one past the end of the document, which callers
    that would write into it treat as an error and callers merely skipping past
    it treat as the end.
    """
    for offset in range(index + 1, len(lines)):
        if closes(fence, lines[offset]):
            return offset + 1
    return len(lines) + 1
