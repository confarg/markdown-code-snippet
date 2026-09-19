# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Parsing an annotation comment."""

from __future__ import annotations

import pytest

from markdown_code_snippet._annotation import (
    looks_like_annotation,
    parse,
)
from markdown_code_snippet.exceptions import AnnotationError


class TestRecognition:
    @pytest.mark.parametrize(
        "line",
        [
            "<!-- snippet: a.yaml -->",
            "<!--snippet:a.yaml-->",
            "    <!-- snippet: a.yaml -->",
            "\t<!-- snippet:   a.yaml   -->",
            "<!--   snippet : a.yaml -->",
        ],
    )
    def test_accepts_spacing_variants(self, line):
        assert looks_like_annotation(line)
        assert parse(line, 1).path == "a.yaml"

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "# A heading",
            "<!-- an ordinary comment -->",
            "<!-- snippets: a.yaml -->",
            "the word snippet: appears in prose",
            "```yaml",
            # Naming an annotation in prose, a table or a code span has to stay
            # ordinary content, or the tool's own documentation could not
            # mention its syntax outside a fenced block.
            "| `<!-- snippet: a.yaml -->` | the whole file |",
            "Write `<!-- snippet: a.yaml -->` above the block.",
            "text <!-- snippet: a.yaml -->",
        ],
    )
    def test_ignores_everything_else(self, line):
        assert not looks_like_annotation(line)

    @pytest.mark.parametrize(
        "line",
        [
            "<!-- snippet: a.yaml --> text",
            "    <!-- snippet: a.yaml --> text",
            "<!-- snippet: a.yaml --><!-- snippet: b.yaml -->",
        ],
    )
    def test_rejects_an_annotation_sharing_its_line(self, line):
        # A typo must not read as prose: it would stop the snippet updating
        # and nothing would ever say so.
        assert looks_like_annotation(line)
        with pytest.raises(AnnotationError, match="alone on its line"):
            parse(line, 7)


class TestTarget:
    def test_a_bare_path_selects_the_whole_file(self):
        annotation = parse("<!-- snippet: dir/a.yaml -->", 1)

        assert annotation.path == "dir/a.yaml"
        assert annotation.selector is None

    def test_a_fragment_is_the_selector(self):
        annotation = parse("<!-- snippet: src/models.py#User -->", 1)

        assert annotation.path == "src/models.py"
        assert annotation.selector == "User"

    def test_a_dotted_fragment_is_kept_whole(self):
        annotation = parse("<!-- snippet: m.py#Team.Invite.accept -->", 1)

        assert annotation.selector == "Team.Invite.accept"

    def test_records_indentation(self):
        annotation = parse("    <!-- snippet: a.yaml -->", 1)

        assert annotation.indent == "    "

    def test_records_its_line_number(self):
        assert parse("<!-- snippet: a.yaml -->", 42).line == 42

    def test_rejects_a_missing_target(self):
        with pytest.raises(AnnotationError, match="must name a file"):
            parse("<!-- snippet: -->", 1)

    def test_rejects_a_fragment_with_no_path(self):
        with pytest.raises(AnnotationError, match="names no file"):
            parse("<!-- snippet: #User -->", 1)

    def test_rejects_a_path_with_an_empty_fragment(self):
        with pytest.raises(AnnotationError, match="names nothing"):
            parse("<!-- snippet: a.py# -->", 1)


class TestOptions:
    def test_defaults(self):
        annotation = parse("<!-- snippet: a.yaml -->", 1)

        assert annotation.lang is None
        assert annotation.dedent is True

    def test_lang(self):
        assert parse("<!-- snippet: a.conf lang=ini -->", 1).lang == "ini"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("true", True), ("false", False), ("TRUE", True), ("False", False)],
    )
    def test_dedent(self, value, expected):
        line = f"<!-- snippet: a.py#f dedent={value} -->"

        assert parse(line, 1).dedent is expected

    def test_a_quoted_value_keeps_its_spaces(self):
        line = '<!-- snippet: a.txt lang="text linenums=1" -->'

        assert parse(line, 1).lang == "text linenums=1"

    def test_a_hash_in_a_value_is_not_a_comment(self):
        # shlex would treat # as a comment character if it were left enabled,
        # and the target itself is full of them.
        line = "<!-- snippet: a.py#f lang=python -->"

        assert parse(line, 1).selector == "f"

    def test_rejects_an_unknown_option(self):
        with pytest.raises(AnnotationError, match="unknown option 'title'"):
            parse('<!-- snippet: a.yaml title="x" -->', 1)

    def test_rejects_a_bare_word(self):
        with pytest.raises(AnnotationError, match="not an option"):
            parse("<!-- snippet: a.yaml dedent -->", 1)

    def test_rejects_a_repeated_option(self):
        with pytest.raises(AnnotationError, match="given twice"):
            parse("<!-- snippet: a.py#f dedent=true dedent=false -->", 1)

    def test_rejects_a_non_boolean_dedent(self):
        with pytest.raises(AnnotationError, match="not a boolean"):
            parse("<!-- snippet: a.py#f dedent=yes -->", 1)

    def test_rejects_an_unbalanced_quote(self):
        with pytest.raises(AnnotationError, match="unquotable"):
            parse('<!-- snippet: a.yaml lang="ini -->', 1)


def test_errors_carry_the_line_number():
    with pytest.raises(AnnotationError) as raised:
        parse("<!-- snippet: -->", 13)

    assert raised.value.line == 13
    assert "line 13" in str(raised.value)
