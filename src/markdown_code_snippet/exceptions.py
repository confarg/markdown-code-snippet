# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Errors raised when a snippet cannot be produced.

Every error carries the Markdown document and the line of the annotation that
failed. Extraction knows neither, so it raises the error without a location and
the processing of that annotation attaches one as the error travels outwards.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from pathlib import Path


class SnippetError(Exception):
    """Base class for every failure this library reports.

    Attributes:
        detail: What went wrong, with no location attached.
        document: The Markdown file carrying the annotation, once known.
        line: The annotation's 1-based line number, once known.

    Dev Notes:
        docs-dev/architecture/03-extraction.md#errors-carry-a-location
    """

    def __init__(self, detail: str) -> None:
        """Build an error that has not been located yet."""
        super().__init__(detail)
        self.detail = detail
        self.document: Path | None = None
        self.line: int | None = None

    def __str__(self) -> str:
        """Return the message, prefixed with a location once there is one."""
        if self.document is not None:
            return f"{self.document}:{self.line}: {self.detail}"
        if self.line is not None:
            return f"line {self.line}: {self.detail}"
        return self.detail

    def located(self, line: int) -> Self:
        """Return this error with the annotation's line number recorded.

        Shaped to be used inline, as ``raise SomeError(...).located(line)``,
        by code that knows which annotation it is reading but not which
        document the annotation came from.
        """
        if self.line is None:
            self.line = line
        return self

    def in_document(self, document: Path) -> None:
        """Attach the document the failing annotation was read from.

        The innermost location wins: an error already carrying a document was
        raised for a nested document and must not be re-labelled here.
        """
        if self.document is None:
            self.document = document


class AnnotationError(SnippetError):
    """An annotation comment is malformed."""


class UnclosedBlock(SnippetError):
    """The code block belonging to an annotation is never closed."""

    def __init__(self) -> None:
        """Build the error for a block with no closing fence."""
        super().__init__(
            "the code block opened below this annotation is never closed",
        )


class RootNotFound(SnippetError):
    """A root-relative path was used, but no project root was found."""

    def __init__(self, path: str) -> None:
        """Build the error for a root-relative path with no root."""
        super().__init__(
            f"{path!r} is root-relative, but no project root was found"
            " (no pyproject.toml, .git or .jj above the document)"
            " -- pass --root to name one",
        )


class AbsolutePath(SnippetError):
    """A snippet path is absolute, which would not survive a clone."""

    def __init__(self, path: str) -> None:
        """Build the error for a path that is not relative."""
        super().__init__(
            f"{path!r} is an absolute path; write it relative to the document,"
            " or as /-prefixed and relative to the project root",
        )


class TargetNotFound(SnippetError):
    """A snippet points at a file that does not exist."""

    def __init__(self, path: Path) -> None:
        """Build the error for a target that does not exist."""
        super().__init__(f"no such file: {path}")


class SourceUnreadable(SnippetError):
    """A source file exists but cannot be read as UTF-8 text."""

    def __init__(self, path: Path, reason: str) -> None:
        """Build the error for a file that cannot be decoded."""
        super().__init__(f"cannot read {path}: {reason}")


class SourceUnparsable(SnippetError):
    """A Python source file cannot be parsed."""

    def __init__(self, path: Path, reason: str, line: int | None) -> None:
        """Build the error for a file that will not parse."""
        where = f" at line {line}" if line is not None else ""
        super().__init__(f"cannot parse {path}{where}: {reason}")


class SelectorUnsupported(SnippetError):
    """A selector was given for a file type that has no selectors."""

    def __init__(self, path: Path, selector: str) -> None:
        """Build the error for a selector on a file that has none."""
        super().__init__(
            f"{path.name} has no selectors, so {selector!r} cannot be"
            " resolved; only .py files can be addressed by symbol",
        )


class SelectorNotFound(SnippetError):
    """A selector names something the source file does not define."""

    def __init__(self, path: Path, selector: str, available: list[str]) -> None:
        """Build the error for a name the file does not define."""
        known = ", ".join(available) if available else "nothing"
        super().__init__(
            f"{path.name} defines no {selector!r}; available here: {known}",
        )


class SelectorNotAScope(SnippetError):
    """A dotted selector tried to descend into something with no body."""

    def __init__(self, path: Path, selector: str, part: str) -> None:
        """Build the error for a selector descending into a value."""
        super().__init__(
            f"{selector!r} descends into {part!r}, which is not a class or a"
            f" function in {path.name}",
        )


class AmbiguousSelector(SnippetError):
    """A selector matches more than one definition.

    Dev Notes:
        docs-dev/architecture/06-design-decisions.md#an-ambiguous-selector-fails
    """

    def __init__(self, path: Path, selector: str, lines: list[int]) -> None:
        """Build the error for a name defined more than once."""
        where = ", ".join(str(line) for line in lines)
        super().__init__(
            f"{selector!r} is defined {len(lines)} times in {path.name}"
            f" (lines {where}), so the selector is ambiguous",
        )
