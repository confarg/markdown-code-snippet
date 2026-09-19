# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The pipeline: scan a document, extract each region, splice the result back.

``--check`` and a rewrite take the same path through here and differ only in
whether the result reaches the disk. Any divergence would let ``--check`` pass
on a file the rewrite would change, which is the one thing a gate must not do.

Dev Notes:
    docs-dev/architecture/05-invariants.md#fragile-couplings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_code_snippet import _text
from markdown_code_snippet._document import Region, scan
from markdown_code_snippet._extract import extract
from markdown_code_snippet._lang import language_for
from markdown_code_snippet._render import render
from markdown_code_snippet._resolve import find_root, resolve
from markdown_code_snippet.exceptions import SnippetError

if TYPE_CHECKING:
    from pathlib import Path


def process_text(
    text: str,
    *,
    document: Path,
    root: Path | None = None,
) -> str:
    """Return a document with every snippet re-read from its source.

    Args:
        text: The document's current content.
        document: Where the document lives. Paths resolve against its
            directory, and errors are reported against it.
        root: The project root, for ``/``-prefixed paths. Looked up from the
            document's own location when omitted.

    Returns:
        The processed document, or ``text`` unchanged when it holds no
        annotation at all.

    Raises:
        SnippetError: Any annotation could not be turned into a block. Nothing
            is spliced unless every region succeeded.
    """
    try:
        return _process(text, document, root)
    except SnippetError as error:
        error.in_document(document)
        raise


def process_file(path: Path, *, root: Path | None = None) -> bool:
    """Rewrite a document in place if any of its snippets is out of date.

    Returns:
        Whether the file was written.
    """
    original, updated = _rendered(path, root)
    if updated == original:
        return False
    _text.write(path, updated)
    return True


def check_file(path: Path, *, root: Path | None = None) -> bool:
    """Return whether a document has snippets that are out of date.

    Writes nothing. Shares every step with :func:`process_file` except the
    write itself.
    """
    original, updated = _rendered(path, root)
    return updated != original


def _rendered(path: Path, root: Path | None) -> tuple[str, str]:
    """Return a document's current text and what it should be."""
    original = _text.read(path)
    return original, process_text(original, document=path, root=root)


def _process(text: str, document: Path, root: Path | None) -> str:
    """Do the work of :func:`process_text`, with no error decoration."""
    lines = _text.normalize(text).split("\n")
    regions = scan(lines)
    if not regions:
        return text

    base = root if root is not None else find_root(document.parent)
    blocks = [_block(region, document, base) for region in regions]
    return _splice(lines, regions, blocks)


def _block(
    region: Region,
    document: Path,
    root: Path | None,
) -> list[str]:
    """Return the block lines one region should hold."""
    annotation = region.annotation
    try:
        path = resolve(annotation.path, document=document, root=root)
        content = extract(
            path,
            annotation.selector,
            dedent=annotation.dedent,
        )
        return render(
            content,
            fence=region.fence,
            lang=annotation.lang or language_for(path),
            indent=annotation.indent,
        )
    except SnippetError as error:
        error.located(annotation.line)
        raise


def _splice(
    lines: list[str],
    regions: list[Region],
    blocks: list[list[str]],
) -> str:
    """Replace each region's span with its block and rejoin the document."""
    out: list[str] = []
    cursor = 0
    for region, block in zip(regions, blocks, strict=True):
        out.extend(lines[cursor : region.start])
        out.extend(block)
        cursor = region.stop
    out.extend(lines[cursor:])
    # A document the tool writes ends with exactly one newline, so that
    # end-of-file-fixer never has anything left to change.
    return "\n".join(out).rstrip("\n") + "\n"
