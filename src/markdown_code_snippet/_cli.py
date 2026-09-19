# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The command line, which is also the pre-commit hook.

Exit codes follow what pre-commit expects of a formatting hook: ``0`` when
there was nothing to do, ``1`` when a file was rewritten or is out of date, and
``2`` when an annotation could not be resolved at all.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdown_code_snippet._process import check_file, process_file
from markdown_code_snippet.exceptions import SnippetError

OK = 0
CHANGED = 1
FAILED = 2

_DESCRIPTION = """
Inject code snippets into Markdown files, in place. Each snippet is introduced
by an HTML comment naming the file to read, and optionally a symbol inside it:
<!-- snippet: src/app.py#main -->
"""


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser, so tests and docs can read it."""
    parser = argparse.ArgumentParser(
        prog="markdown-code-snippet",
        description=_DESCRIPTION,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        metavar="PATH",
        help="Markdown files, or directories to search for *.md",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report out-of-date snippets without writing anything",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        metavar="DIR",
        help="the directory /-prefixed snippet paths resolve against"
        " (default: the nearest pyproject.toml, .git or .jj)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Process the documents named on the command line."""
    args = build_parser().parse_args(argv)
    root = args.root.resolve() if args.root is not None else None

    changed: list[Path] = []
    failed = False
    for document in documents(args.paths):
        try:
            stale = (
                check_file(document, root=root)
                if args.check
                else process_file(document, root=root)
            )
        except SnippetError as error:
            print(error, file=sys.stderr)
            failed = True
            continue
        if stale:
            changed.append(document)
            verb = "out of date" if args.check else "rewrote"
            print(f"{verb}: {document}")

    if failed:
        return FAILED
    return CHANGED if changed else OK


def documents(paths: list[Path]) -> list[Path]:
    """Expand the paths given on the command line into Markdown files.

    A directory contributes every ``*.md`` below it, sorted. Duplicates are
    dropped, because pre-commit may pass the same file twice.
    """
    found: dict[Path, None] = {}
    for path in paths:
        if path.is_dir():
            for markdown in sorted(path.rglob("*.md")):
                found[markdown] = None
        else:
            found[path] = None
    return list(found)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
