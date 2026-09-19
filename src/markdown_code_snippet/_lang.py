# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Guessing a fence language from a file name.

Consulted in one situation only: the tool has to create a fence the author did
not write, and needs an info string for it. An existing fence is never
re-labelled.

Dev Notes:
    docs-dev/architecture/06-design-decisions.md#the-author-owns-the-fence-line
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

#: What a code block gets when nothing else matches. A fence with no info
#: string would also work, but a highlighter that guesses is worse than one
#: that is told not to.
FALLBACK = "text"

BY_SUFFIX = {
    ".bash": "bash",
    ".c": "c",
    ".cfg": "ini",
    ".cpp": "cpp",
    ".css": "css",
    ".diff": "diff",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".ini": "ini",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsonc": "json",
    ".kt": "kotlin",
    ".lua": "lua",
    ".md": "markdown",
    ".patch": "diff",
    ".php": "php",
    ".ps1": "powershell",
    ".py": "python",
    ".pyi": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "bash",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".txt": "text",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".zsh": "bash",
}

#: Files that carry their type in their name rather than in a suffix.
BY_NAME = {
    ".editorconfig": "ini",
    ".gitignore": "gitignore",
    "CMakeLists.txt": "cmake",
    "Dockerfile": "dockerfile",
    "Justfile": "just",
    "Makefile": "makefile",
    "justfile": "just",
}


def language_for(path: Path) -> str:
    """Return the info string to give a fence created for this file."""
    by_name = BY_NAME.get(path.name)
    if by_name is not None:
        return by_name
    return BY_SUFFIX.get(path.suffix.lower(), FALLBACK)
