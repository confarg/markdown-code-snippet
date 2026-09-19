# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Scanning a document into regions, and the fence handling it rests on."""

from __future__ import annotations

import pytest

from markdown_code_snippet._document import (
    Fence,
    closes,
    match_fence,
    scan,
)
from markdown_code_snippet.exceptions import AnnotationError, UnclosedBlock


def lines(text: str) -> list[str]:
    return text.split("\n")


class TestFences:
    @pytest.mark.parametrize(
        ("line", "char", "length", "info"),
        [
            ("```", "`", 3, ""),
            ("```python", "`", 3, "python"),
            ('`````yaml title="a"', "`", 5, 'yaml title="a"'),
            ("~~~ini", "~", 3, "ini"),
            ("    ```py", "`", 3, "py"),
        ],
    )
    def test_taken_apart(self, line, char, length, info):
        fence = match_fence(line)

        assert fence is not None
        assert (fence.char, fence.length, fence.info) == (char, length, info)

    @pytest.mark.parametrize("line", ["``", "~~", "text", "", "  ``x"])
    def test_not_a_fence(self, line):
        assert match_fence(line) is None

    def test_round_trips_the_line_it_came_from(self):
        line = '    ````markdown title="x"'

        rebuilt = match_fence(line)

        assert rebuilt is not None
        assert rebuilt.line == line


class TestClosing:
    @pytest.fixture
    def fence(self):
        return Fence(indent="", char="`", length=3, info="python")

    @pytest.mark.parametrize("line", ["```", "````", "    ```", "```   "])
    def test_closes(self, fence, line):
        assert closes(fence, line)

    @pytest.mark.parametrize(
        "line",
        ["``", "~~~", "```python", "text", "``` x"],
    )
    def test_does_not_close(self, fence, line):
        assert not closes(fence, line)

    def test_a_longer_fence_needs_a_longer_closer(self):
        fence = Fence(indent="", char="`", length=4, info="markdown")

        assert not closes(fence, "```")
        assert closes(fence, "````")


class TestScanning:
    def test_finds_nothing_in_a_plain_document(self):
        assert scan(lines("# Title\n\nSome prose.\n")) == []

    def test_a_region_spans_its_block(self):
        document = lines(
            "# Title\n<!-- snippet: a.yaml -->\n```yaml\nold\n```\nafter\n",
        )

        [region] = scan(document)

        assert region.annotation.path == "a.yaml"
        assert region.fence is not None
        assert (region.start, region.stop) == (2, 5)
        assert document[region.stop] == "after"

    def test_an_annotation_with_no_block_is_an_empty_span(self):
        document = lines("<!-- snippet: a.yaml -->\n\nprose\n")

        [region] = scan(document)

        assert region.fence is None
        assert region.start == region.stop == 1

    def test_an_annotation_on_the_last_line(self):
        document = lines("prose\n<!-- snippet: a.yaml -->")

        [region] = scan(document)

        assert region.fence is None
        assert region.start == region.stop == len(document)

    def test_a_block_is_not_adopted_across_a_blank_line(self):
        document = lines(
            "<!-- snippet: a.yaml -->\n\n```yaml\nkept\n```\n",
        )

        [region] = scan(document)

        assert region.fence is None
        assert region.start == region.stop == 1

    def test_an_annotation_inside_a_fence_is_content(self):
        document = lines(
            "````markdown\n"
            "<!-- snippet: a.yaml -->\n"
            "```yaml\n"
            "host: localhost\n"
            "```\n"
            "````\n",
        )

        assert scan(document) == []

    def test_an_annotation_inside_an_unowned_block_of_any_length(self):
        document = lines(
            "~~~~\n<!-- snippet: a.yaml -->\n~~~\nstill inside\n~~~~\n",
        )

        assert scan(document) == []

    def test_a_region_block_may_contain_shorter_fences(self):
        document = lines(
            "<!-- snippet: r.md -->\n"
            "````markdown\n"
            "```bash\n"
            "run\n"
            "```\n"
            "````\n"
            "after\n",
        )

        [region] = scan(document)

        assert (region.start, region.stop) == (1, 6)

    def test_several_regions_in_order(self):
        document = lines(
            "<!-- snippet: a.yaml -->\n"
            "```yaml\n"
            "```\n"
            "prose\n"
            "<!-- snippet: b.py#f -->\n"
            "```python\n"
            "```\n",
        )

        first, second = scan(document)

        assert first.annotation.path == "a.yaml"
        assert second.annotation.selector == "f"
        assert first.stop <= second.start

    def test_a_region_whose_block_is_never_closed(self):
        document = lines("<!-- snippet: a.yaml -->\n```yaml\nno closer\n")

        with pytest.raises(UnclosedBlock, match="never closed"):
            scan(document)

    def test_an_unowned_unclosed_block_swallows_the_rest(self):
        # The document is already broken; the point is that the tool does not
        # write into it, not that it repairs it.
        document = lines("```yaml\n<!-- snippet: a.yaml -->\nno closer\n")

        assert scan(document) == []

    def test_a_malformed_annotation_stops_the_scan(self):
        document = lines("<!-- snippet: a.yaml --> and then prose\n")

        with pytest.raises(AnnotationError):
            scan(document)

    def test_an_annotation_named_mid_line_is_prose(self):
        # A table cell or a code span naming the syntax is content, which is
        # what lets this project document itself outside a fenced block.
        document = lines("| `<!-- snippet: a.yaml -->` | whole file |\n")

        assert scan(document) == []
