# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Dispatch from a selector to the extractor that understands it.

A selector names either a region the file marks out with comments, or, in a
Python file, a definition. The two are told apart here, and a name that both
could answer to is an error rather than a silent choice. The scanner and the
renderer are untouched by either.

Dev Notes:
    docs-dev/architecture/03-extraction.md
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from markdown_code_snippet._extract._python import extract_symbol, symbol_line
from markdown_code_snippet._extract._region import find_regions
from markdown_code_snippet._extract._whole import extract_whole
from markdown_code_snippet.exceptions import (
    SelectorNamesTwice,
    SelectorNotFound,
    SelectorUnsupported,
)

if TYPE_CHECKING:
    from pathlib import Path

#: Suffixes whose definitions a selector can name. Everything else can be
#: addressed only by a region it marks out, or included whole.
_SYMBOL_SUFFIXES = frozenset({".py", ".pyi"})


def extract(
    path: Path,
    selector: str | None,
    *,
    dedent: bool = True,
) -> str:
    """Return the text a target names.

    Args:
        path: The resolved source file.
        selector: What to extract, or None for the whole file.
        dedent: Whether to strip the result's common leading indentation.

    Raises:
        SnippetError: The file cannot be read, or the selector cannot be
            resolved against it.
    """
    if selector is None:
        content = extract_whole(path)
    else:
        content = _named(path, selector)

    return textwrap.dedent(content) if dedent else content


def _named(path: Path, selector: str) -> str:
    """Return what a selector names: a marked region, or a Python definition."""
    regions = find_regions(path)
    is_python = path.suffix.lower() in _SYMBOL_SUFFIXES

    if selector not in regions:
        if is_python:
            return extract_symbol(path, selector)
        if regions:
            raise SelectorNotFound(path, selector, sorted(regions))
        raise SelectorUnsupported(path, selector)

    region = regions[selector]
    if is_python:
        definition = symbol_line(path, selector)
        if definition is not None:
            raise SelectorNamesTwice(path, selector, region.opened, definition)
    return region.body
