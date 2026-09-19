# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Turning extracted content into the lines of a code block.

Dev Notes:
    docs-dev/architecture/02-scanning-and-splicing.md#fence-escalation
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from markdown_code_snippet._document import Fence

if TYPE_CHECKING:
    from collections.abc import Iterable

#: The shortest fence Markdown allows.
MINIMUM = 3

_RUNS = {
    "`": re.compile(r"^[ \t]*(`+)"),
    "~": re.compile(r"^[ \t]*(~+)"),
}


def render(
    content: str,
    *,
    fence: Fence | None,
    lang: str,
    indent: str,
) -> list[str]:
    """Return the lines of the block a region should hold.

    Args:
        content: The extracted text, already dedented.
        fence: The author's opening fence, or None if there is no block yet.
        lang: The info string to give a fence that has to be created.
        indent: The annotation's indentation, used for a created fence.

    Returns:
        The opening fence, the body, and the closing fence.
    """
    base = fence or Fence(indent=indent, char="`", length=MINIMUM, info=lang)
    body = body_lines(content, base.indent)
    length = fence_length(body, base.char, base.length)
    opening = Fence(base.indent, base.char, length, base.info)
    return [opening.line, *body, f"{base.indent}{base.char * length}"]


def body_lines(content: str, indent: str) -> list[str]:
    """Return the body lines for some content, indented and stripped.

    Trailing whitespace goes, blank lines at either end go, and every remaining
    line is indented to sit under its fence. Blank lines stay empty rather than
    becoming runs of spaces: anything else fights the ``trailing-whitespace``
    hook, and a hook that cannot agree with its neighbours never terminates.
    """
    stripped = [line.rstrip() for line in content.split("\n")]
    start, stop = 0, len(stripped)
    while start < stop and not stripped[start]:
        start += 1
    while stop > start and not stripped[stop - 1]:
        stop -= 1
    return [f"{indent}{line}" if line else "" for line in stripped[start:stop]]


def fence_length(body: Iterable[str], char: str, minimum: int) -> int:
    """Return how many fence characters enclose this body.

    One more than the longest run the body opens a line with, since only a
    line-initial run can close a fence, and never shorter than the fence the
    author already wrote.
    """
    pattern = _RUNS[char]
    longest = 0
    for line in body:
        found = pattern.match(line)
        if found is not None:
            longest = max(longest, len(found.group(1)))
    return max(MINIMUM, minimum, longest + 1)
