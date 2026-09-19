# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The pipeline: process_text, process_file and check_file."""

from __future__ import annotations

import pytest

from markdown_code_snippet import check_file, process_file, process_text
from markdown_code_snippet.exceptions import TargetNotFound


@pytest.fixture
def source(root, write):
    """A source file to point at, and the document's directory beside it."""
    write("docs/config.yaml", "host: localhost\nport: 8080\n")
    return root


def document(root, text):
    """Write a document into the project's docs/ directory."""
    path = root / "docs" / "doc.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


class TestProcessText:
    def test_a_document_with_no_annotation_is_returned_untouched(self, root):
        original = "# Title\r\n\r\nNo final newline and CRLF endings"

        assert process_text(original, document=root / "a.md") == original

    def test_a_block_is_filled(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n")

        result = process_text(path.read_text(), document=path)

        assert result == (
            "<!-- snippet: config.yaml -->\n"
            "```yaml\n"
            "host: localhost\n"
            "port: 8080\n"
            "```\n"
        )

    def test_the_annotation_line_is_preserved_byte_for_byte(self, source):
        annotation = "<!--snippet:config.yaml   lang=yaml-->"
        path = document(source, f"{annotation}\n")

        result = process_text(path.read_text(), document=path)

        assert result.splitlines()[0] == annotation

    def test_prose_around_a_region_is_untouched(self, source):
        path = document(
            source,
            "before\n\n<!-- snippet: config.yaml -->\n"
            "```yaml\nold\n```\n\nafter\n",
        )

        result = process_text(path.read_text(), document=path)

        assert result.startswith("before\n\n")
        assert result.endswith("```\n\nafter\n")

    def test_a_document_that_ends_inside_a_region_gains_a_newline(
        self,
        source,
    ):
        path = document(source, "prose\n<!-- snippet: config.yaml -->")

        result = process_text(path.read_text(), document=path)

        assert result.endswith("```\n")

    def test_extra_trailing_newlines_are_collapsed(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n\n\n\n")

        result = process_text(path.read_text(), document=path)

        assert result.endswith("```\n")
        assert not result.endswith("\n\n")

    def test_nothing_is_written_if_a_later_region_fails(self, source):
        # A document is spliced only once every region has been extracted.
        path = document(
            source,
            "<!-- snippet: config.yaml -->\n"
            "```yaml\n"
            "old\n"
            "```\n"
            "<!-- snippet: absent.yaml -->\n",
        )
        before = path.read_bytes()

        with pytest.raises(TargetNotFound, match="no such file"):
            process_file(path)

        assert path.read_bytes() == before

    def test_the_root_is_looked_up_from_the_document(self, root, write):
        write("lib/app.py", "VALUE = 1\n")
        path = document(root, "<!-- snippet: /lib/app.py#VALUE -->\n")

        result = process_text(path.read_text(), document=path)

        assert "VALUE = 1" in result

    def test_an_explicit_root_wins(self, tmp_path, write):
        write("elsewhere/lib/app.py", "VALUE = 2\n")
        write("project/pyproject.toml", "")
        path = tmp_path / "project" / "doc.md"
        path.write_bytes(b"<!-- snippet: /lib/app.py#VALUE -->\n")

        result = process_text(
            path.read_text(),
            document=path,
            root=tmp_path / "elsewhere",
        )

        assert "VALUE = 2" in result


class TestProcessFile:
    def test_reports_that_it_wrote(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n")

        assert process_file(path) is True
        assert "host: localhost" in path.read_text()

    def test_reports_that_it_had_nothing_to_do(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n")
        process_file(path)

        assert process_file(path) is False

    def test_a_document_with_no_annotation_is_never_written(self, root):
        path = document(root, "# Title\r\nno final newline")
        before = path.read_bytes()

        assert process_file(path) is False
        assert path.read_bytes() == before

    def test_output_uses_lf_even_on_windows(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n")

        process_file(path)

        assert b"\r\n" not in path.read_bytes()

    def test_a_stale_body_is_replaced_not_appended(self, source):
        path = document(
            source,
            "<!-- snippet: config.yaml -->\n```yaml\nstale\n```\n",
        )

        process_file(path)

        assert "stale" not in path.read_text()


class TestCheckFile:
    def test_reports_staleness_without_writing(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n")
        before = path.read_bytes()

        assert check_file(path) is True
        assert path.read_bytes() == before

    def test_agrees_with_process_file(self, source):
        path = document(source, "<!-- snippet: config.yaml -->\n")

        assert check_file(path) is True
        process_file(path)
        assert check_file(path) is False
