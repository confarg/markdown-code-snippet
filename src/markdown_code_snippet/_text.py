# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Reading and writing text, and the line-ending rules that come with it.

The one place bytes become text and text becomes bytes. Python's text mode
translates line endings per platform, which would make a document written on
Windows differ from the same document written on Linux; reading and writing
bytes and normalizing here keeps the output identical everywhere.

Dev Notes:
    docs-dev/architecture/02-scanning-and-splicing.md#whitespace
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_code_snippet.exceptions import SourceUnreadable, TargetNotFound

if TYPE_CHECKING:
    from pathlib import Path


def normalize(text: str) -> str:
    """Return text with CRLF and CR line endings turned into LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read(path: Path) -> str:
    """Return a file's text, normalized.

    Raises:
        TargetNotFound: The file does not exist.
        SourceUnreadable: The file is not readable, or is not valid UTF-8.
    """
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise TargetNotFound(path) from None
    except OSError as error:
        raise SourceUnreadable(path, error.strerror or str(error)) from None

    try:
        return normalize(raw.decode("utf-8"))
    except UnicodeDecodeError as error:
        reason = f"not valid UTF-8 ({error.reason})"
        raise SourceUnreadable(path, reason) from None


def write(path: Path, text: str) -> None:
    """Write text as UTF-8 with LF endings, bypassing platform translation."""
    path.write_bytes(text.encode("utf-8"))
