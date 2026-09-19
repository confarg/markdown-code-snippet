# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Extracting an entire file.

Dev Notes:
    docs-dev/architecture/03-extraction.md#whole-file
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_code_snippet import _text

if TYPE_CHECKING:
    from pathlib import Path


def extract_whole(path: Path) -> str:
    """Return a file's whole text.

    Blank lines at either end are dropped by the renderer, which does it for
    every extractor at once.
    """
    return _text.read(path)
