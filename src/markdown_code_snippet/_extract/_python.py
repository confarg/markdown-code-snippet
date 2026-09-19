# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Locating a Python definition statically and slicing it out of its file.

Dev Notes:
    docs-dev/architecture/03-extraction.md#python-symbols
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from markdown_code_snippet import _text
from markdown_code_snippet.exceptions import (
    AmbiguousSelector,
    SelectorNotAScope,
    SelectorNotFound,
    SourceUnparsable,
)

if TYPE_CHECKING:
    from pathlib import Path

#: Statements a dotted selector can descend into. Which statements a selector
#: can *name* is decided by :func:`_defined_names`, which also has to say what
#: name each one binds.
_SCOPE = ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef

#: How many sibling names an error message lists before giving up.
_LISTED = 12

Scope = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


def extract_symbol(path: Path, selector: str) -> str:
    """Return the source of the definition a selector names.

    Raises:
        SourceUnparsable: The file is not valid Python.
        SelectorNotFound: Nothing of that name is defined.
        SelectorNotAScope: A dotted selector descends into a non-scope.
        AmbiguousSelector: More than one definition carries the name.
    """
    source = _text.read(path)
    lines = source.split("\n")
    node = _find(_tree(path, source), path, selector)
    first, last = _span(node, lines)
    return "\n".join(lines[first - 1 : last])


def _tree(path: Path, source: str) -> ast.Module:
    """Parse a source file, reporting a syntax error as a snippet error."""
    try:
        return ast.parse(source)
    except SyntaxError as error:
        raise SourceUnparsable(path, error.msg, error.lineno) from None


def _find(tree: ast.Module, path: Path, selector: str) -> ast.stmt:
    """Return the single statement a dotted selector names."""
    parts = selector.split(".")
    scope: Scope = tree
    for depth, part in enumerate(parts):
        node = _one(scope, part, path, selector)
        if depth == len(parts) - 1:
            return node
        if not isinstance(node, _SCOPE):
            raise SelectorNotAScope(path, selector, part)
        scope = node
    raise SelectorNotFound(path, selector, [])  # pragma: no cover - parts>=1


def _one(scope: Scope, name: str, path: Path, selector: str) -> ast.stmt:
    """Return the only statement in ``scope`` defining ``name``."""
    found = [node for node in scope.body if _defines(node, name)]
    if not found:
        raise SelectorNotFound(path, selector, _siblings(scope))
    if len(found) > 1:
        raise AmbiguousSelector(
            path,
            selector,
            [node.lineno for node in found],
        )
    return found[0]


def _defines(node: ast.stmt, name: str) -> bool:
    """Return whether a statement defines ``name`` in its own scope."""
    return name in _defined_names(node)


def _defined_names(node: ast.stmt) -> list[str]:
    """Return every name a statement binds, in source order."""
    if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
        return [node.name]
    if isinstance(node, ast.AnnAssign):
        return _target_names(node.target)
    if isinstance(node, ast.Assign):
        return [n for target in node.targets for n in _target_names(target)]
    return []


def _target_names(target: ast.expr) -> list[str]:
    """Return the plain names an assignment target binds.

    Attribute and subscript targets bind nothing a selector can name, so
    ``self.x = 1`` and ``d["k"] = 1`` contribute nothing.
    """
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Tuple | ast.List):
        return [n for element in target.elts for n in _target_names(element)]
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return []


def _siblings(scope: Scope) -> list[str]:
    """Return the names defined in a scope, for a not-found message."""
    names = [name for node in scope.body for name in _defined_names(node)]
    if len(names) > _LISTED:
        return [*names[:_LISTED], "..."]
    return names


def _span(node: ast.stmt, lines: list[str]) -> tuple[int, int]:
    """Return the 1-based first and last line of a definition.

    Decorators come first: ``ast`` puts a decorated node's ``lineno`` on its
    ``def`` or ``class`` line, and a decorator is part of what the definition
    means.
    """
    last = node.end_lineno or node.lineno
    decorators = getattr(node, "decorator_list", [])
    if not decorators:
        return node.lineno, last

    earliest = min(decorator.lineno for decorator in decorators)
    return _at_sign(lines, earliest), last


def _at_sign(lines: list[str], expression_line: int) -> int:
    """Return the 1-based line carrying the ``@`` of a decorator.

    A decorator's recorded position is that of the expression after the ``@``,
    which is normally the same line but need not be when the expression is
    parenthesized across lines.
    """
    for index in range(expression_line - 1, -1, -1):
        if lines[index].lstrip().startswith("@"):
            return index + 1
    return expression_line  # pragma: no cover - a decorator always has an @
