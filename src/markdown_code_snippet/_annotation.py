# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Recognizing an annotation line and parsing what it says.

Dev Notes:
    docs-dev/architecture/01-annotation-syntax.md#grammar
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass

from markdown_code_snippet.exceptions import AnnotationError

#: Loose enough to notice that a line *means* to be an annotation, so that a
#: malformed one is reported instead of silently read as prose -- but anchored
#: to the start of the line, so that naming an annotation inside a table cell or
#: a code span stays ordinary prose.
_INTENT = re.compile(r"^[ \t]*<!--\s*snippet\s*:")

#: What a well-formed annotation looks like: alone on its line, nothing but
#: optional indentation before it and whitespace after it. The body cannot
#: cross a ``-->``, or a line carrying two comments would parse as one
#: annotation whose options are the other comment's markup.
_EXACT = re.compile(
    r"^(?P<indent>[ \t]*)<!--\s*snippet\s*:"
    r"(?P<body>(?:(?!-->).)*)-->[ \t]*$",
)

_BOOLEANS = {"true": True, "false": False}

#: Options the tool understands. Everything else that decorates a block is
#: written on the fence line by the author, not passed through here.
_OPTIONS = frozenset({"dedent", "lang"})


@dataclass(frozen=True)
class Annotation:
    """One parsed annotation comment.

    Attributes:
        path: The path as written, before resolution.
        selector: What to extract from the file, or None for the whole file.
        lang: The info string for a fence the tool has to create, if given.
        dedent: Whether to strip the content's common leading indentation.
        indent: The annotation line's own leading whitespace, which the
            generated block inherits.
        line: The annotation's 1-based line number in its document.
    """

    path: str
    selector: str | None
    lang: str | None
    dedent: bool
    indent: str
    line: int


def looks_like_annotation(line: str) -> bool:
    """Return whether a line means to be an annotation, well-formed or not."""
    return _INTENT.search(line) is not None


def parse(line: str, number: int) -> Annotation:
    """Parse one annotation line.

    Args:
        line: The line, without its trailing newline.
        number: Its 1-based position in the document, for error messages.

    Raises:
        AnnotationError: The line is not a well-formed annotation.
    """
    exact = _EXACT.match(line)
    if exact is None:
        raise _alone_on_its_line(number)

    tokens = _split(exact.group("body"), number)
    if not tokens:
        raise _no_target(number)

    path, selector = _target(tokens[0], number)
    options = _parse_options(tokens[1:], number)
    return Annotation(
        path=path,
        selector=selector,
        lang=options.get("lang"),
        dedent=_boolean(options.get("dedent", "true"), "dedent", number),
        indent=exact.group("indent"),
        line=number,
    )


def _split(body: str, number: int) -> list[str]:
    """Split an annotation body into tokens, honouring quoted values."""
    try:
        return shlex.split(body)
    except ValueError as error:
        raise AnnotationError(f"annotation is unquotable: {error}").located(
            number,
        ) from None


def _target(token: str, number: int) -> tuple[str, str | None]:
    """Split the first token into a path and an optional selector."""
    path, hashed, selector = token.partition("#")
    if not path:
        raise AnnotationError(
            f"{token!r} names no file before its '#'",
        ).located(number)
    if hashed and not selector:
        raise AnnotationError(
            f"{token!r} ends in '#' but names nothing to extract",
        ).located(number)
    return path, selector or None


def _parse_options(tokens: list[str], number: int) -> dict[str, str]:
    """Parse the trailing ``key=value`` tokens of an annotation."""
    options: dict[str, str] = {}
    for token in tokens:
        key, equals, value = token.partition("=")
        if not equals:
            raise AnnotationError(
                f"{token!r} is not an option; options read key=value",
            ).located(number)
        if key not in _OPTIONS:
            known = ", ".join(sorted(_OPTIONS))
            raise AnnotationError(
                f"unknown option {key!r}; this tool understands {known}."
                " Everything else that decorates a code block goes on the"
                " fence line itself",
            ).located(number)
        if key in options:
            raise AnnotationError(f"{key!r} is given twice").located(number)
        options[key] = value
    return options


def _boolean(value: str, key: str, number: int) -> bool:
    """Parse a boolean option value."""
    try:
        return _BOOLEANS[value.lower()]
    except KeyError:
        raise AnnotationError(
            f"{key}={value!r} is not a boolean; write true or false",
        ).located(number) from None


def _alone_on_its_line(number: int) -> AnnotationError:
    """Build the error for an annotation sharing its line with something."""
    return AnnotationError(
        "an annotation must be alone on its line; remove what follows"
        " its '-->'",
    ).located(number)


def _no_target(number: int) -> AnnotationError:
    """Build the error for an annotation that names no file."""
    return AnnotationError(
        "an annotation must name a file: <!-- snippet: path/to/file -->",
    ).located(number)
