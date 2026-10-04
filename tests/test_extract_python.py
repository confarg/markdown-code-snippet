# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Locating Python definitions statically."""

from __future__ import annotations

import pytest

from markdown_code_snippet._extract import extract
from markdown_code_snippet._extract._python import extract_symbol
from markdown_code_snippet.exceptions import (
    AmbiguousSelector,
    SelectorNotAScope,
    SelectorNotFound,
    SelectorUnsupported,
    SourceUnparsable,
)

MODULE = '''
"""A module docstring."""

from dataclasses import dataclass
from typing import Final

TOTAL: Final = 3
FIRST, SECOND = 1, 2
counter = 0
counter += 1


def plain(value: int) -> int:
    """Double a value."""
    return value * 2


async def fetched() -> None:
    """Do nothing, asynchronously."""


@dataclass(frozen=True)
class Boxed:
    """A box."""

    value: int = 0

    @property
    def doubled(self) -> int:
        """Twice the value."""
        return self.value * 2

    class Inner:
        """Nested on purpose."""

        def method(self) -> None:
            """Reachable through two dots."""
'''


@pytest.fixture
def module(write):
    return write("mod.py", MODULE)


class TestDefinitions:
    def test_a_function_comes_with_its_docstring(self, module):
        assert extract_symbol(module, "plain") == (
            "def plain(value: int) -> int:\n"
            '    """Double a value."""\n'
            "    return value * 2"
        )

    def test_an_async_function(self, module):
        assert extract_symbol(module, "fetched").startswith("async def")

    def test_a_decorated_class_keeps_its_decorator(self, module):
        extracted = extract_symbol(module, "Boxed")

        assert extracted.startswith("@dataclass(frozen=True)\nclass Boxed:")
        assert extracted.endswith('"""Reachable through two dots."""')

    def test_a_decorated_method(self, module):
        assert extract_symbol(module, "Boxed.doubled") == (
            "    @property\n"
            "    def doubled(self) -> int:\n"
            '        """Twice the value."""\n'
            "        return self.value * 2"
        )

    def test_a_nested_class(self, module):
        assert extract_symbol(module, "Boxed.Inner").startswith(
            "    class Inner:",
        )

    def test_two_dots_deep(self, module):
        assert extract_symbol(module, "Boxed.Inner.method") == (
            "        def method(self) -> None:\n"
            '            """Reachable through two dots."""'
        )

    def test_an_annotated_assignment(self, module):
        assert extract_symbol(module, "TOTAL") == "TOTAL: Final = 3"

    def test_a_plain_assignment(self, module):
        assert extract_symbol(module, "counter") == "counter = 0"

    def test_a_type_statement(self, write):
        source = write(
            "m.py",
            "type Config = int | str\n\n\ndef main() -> None: ...\n",
        )

        assert extract_symbol(source, "Config") == "type Config = int | str"

    def test_a_generic_type_statement(self, write):
        source = write("m.py", "type Pair[T] = tuple[T, T]\n")

        assert extract_symbol(source, "Pair") == "type Pair[T] = tuple[T, T]"

    def test_a_type_statement_inside_a_class(self, write):
        source = write(
            "m.py",
            """
            class Outer:
                type Inner = list[int]
            """,
        )

        assert extract_symbol(source, "Outer.Inner") == (
            "    type Inner = list[int]"
        )

    def test_a_tuple_assignment_yields_the_whole_statement(self, module):
        assert extract_symbol(module, "SECOND") == "FIRST, SECOND = 1, 2"

    def test_a_starred_target(self, write):
        source = write("m.py", "HEAD, *TAIL = [1, 2, 3]\n")

        assert extract_symbol(source, "TAIL") == "HEAD, *TAIL = [1, 2, 3]"

    def test_a_multi_line_value(self, write):
        source = write(
            "m.py",
            """
            DEFAULTS = {
                "host": "localhost",
                "port": 8080,
            }
            """,
        )

        assert extract_symbol(source, "DEFAULTS").endswith("}")


class TestDecorators:
    def test_every_decorator_is_included(self, write):
        source = write(
            "m.py",
            """
            @first
            @second(with_an="argument")
            def target() -> None:
                pass
            """,
        )

        assert extract_symbol(source, "target").startswith("@first\n@second")

    def test_a_decorator_whose_expression_starts_on_a_later_line(self, write):
        # PEP 614 allows any expression after the @, so the recorded position
        # of the decorator is not necessarily the line carrying the @.
        source = write(
            "m.py",
            """
            @(
                first
            )
            def target() -> None:
                pass
            """,
        )

        assert extract_symbol(source, "target").startswith("@(\n")

    def test_a_comment_between_decorators_is_kept(self, write):
        source = write(
            "m.py",
            """
            @first
            # why the second one is needed
            @second
            def target() -> None:
                pass
            """,
        )

        assert "# why the second one is needed" in extract_symbol(
            source,
            "target",
        )

    def test_a_comment_above_the_first_decorator_is_not(self, write):
        source = write(
            "m.py",
            """
            # not part of the definition
            @first
            def target() -> None:
                pass
            """,
        )

        assert extract_symbol(source, "target").startswith("@first")


class TestDedent:
    def test_dedent_normalizes_a_method_to_column_zero(self, module):
        assert extract(module, "Boxed.doubled").startswith("@property\n")

    def test_dedent_false_keeps_the_original_columns(self, module):
        extracted = extract(module, "Boxed.doubled", dedent=False)

        assert extracted.startswith("    @property\n")


class TestFailures:
    def test_an_unknown_name_lists_what_is_there(self, module):
        with pytest.raises(SelectorNotFound) as raised:
            extract_symbol(module, "missing")

        message = str(raised.value)
        assert "defines no 'missing'" in message
        assert "plain" in message
        assert "Boxed" in message

    def test_an_unknown_name_in_a_nested_scope(self, module):
        with pytest.raises(SelectorNotFound, match="doubled"):
            extract_symbol(module, "Boxed.missing")

    def test_a_long_scope_is_truncated(self, write):
        source = write(
            "m.py",
            "\n".join(f"name_{index} = {index}" for index in range(20)),
        )

        with pytest.raises(SelectorNotFound) as raised:
            extract_symbol(source, "missing")

        assert str(raised.value).endswith("...")

    def test_descending_into_an_assignment(self, module):
        with pytest.raises(SelectorNotAScope, match="'TOTAL'"):
            extract_symbol(module, "TOTAL.inner")

    def test_an_augmented_assignment_is_not_addressable(self, module):
        # counter += 1 rebinds a name but defines nothing a reader would quote.
        assert extract_symbol(module, "counter") == "counter = 0"

    def test_an_attribute_target_is_not_addressable(self, write):
        source = write("m.py", "obj.attribute = 1\n")

        with pytest.raises(SelectorNotFound):
            extract_symbol(source, "attribute")

    def test_an_overloaded_function_is_ambiguous(self, write):
        source = write(
            "m.py",
            """
            from typing import overload


            @overload
            def load(path: str) -> int: ...
            @overload
            def load(path: None) -> None: ...
            def load(path):
                return 0
            """,
        )

        with pytest.raises(AmbiguousSelector) as raised:
            extract_symbol(source, "load")

        assert "defined 3 times" in str(raised.value)
        assert "lines 5, 7, 8" in str(raised.value)

    def test_a_name_bound_in_two_branches_is_ambiguous(self, write):
        source = write(
            "m.py",
            """
            VALUE = 1
            VALUE = 2
            """,
        )

        with pytest.raises(AmbiguousSelector, match="lines 1, 2"):
            extract_symbol(source, "VALUE")

    def test_a_syntax_error_names_its_line(self, write):
        source = write("m.py", "def broken(\n")

        with pytest.raises(SourceUnparsable, match="at line 1"):
            extract_symbol(source, "broken")

    def test_a_selector_on_a_file_that_has_none(self, write):
        source = write("config.yaml", "host: localhost\n")

        with pytest.raises(SelectorUnsupported, match="no selectors"):
            extract(source, "server")
