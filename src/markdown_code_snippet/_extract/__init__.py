# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Dispatch from a selector to the extractor that understands it.

This is the seam a new selector kind is added at: named regions and line ranges
both belong here, behind the same signature, leaving the scanner and the
renderer untouched.

Dev Notes:
    docs-dev/architecture/03-extraction.md
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from markdown_code_snippet._extract._python import extract_symbol
from markdown_code_snippet._extract._whole import extract_whole
from markdown_code_snippet.exceptions import SelectorUnsupported

if TYPE_CHECKING:
    from pathlib import Path

#: Suffixes whose symbols a selector can name. Everything else is whole-file
#: only, because a selector there would need a parser for that language.
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
    elif path.suffix.lower() in _SYMBOL_SUFFIXES:
        content = extract_symbol(path, selector)
    else:
        raise SelectorUnsupported(path, selector)

    return textwrap.dedent(content) if dedent else content
