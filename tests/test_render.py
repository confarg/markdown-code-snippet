# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Building a code block out of extracted content."""

from __future__ import annotations

import pytest

from markdown_code_snippet._document import Fence
from markdown_code_snippet._render import body_lines, fence_length, render


class TestBody:
    def test_trailing_whitespace_goes(self):
        # Otherwise trailing-whitespace strips it and the next run of this hook
        # puts it back, and pre-commit never converges.
        assert body_lines("a   \nb\t\n", "") == ["a", "b"]

    def test_blank_lines_at_either_end_go(self):
        assert body_lines("\n\na\n\n\n", "") == ["a"]

    def test_blank_lines_inside_stay(self):
        assert body_lines("a\n\nb\n", "") == ["a", "", "b"]

    def test_indentation_is_applied(self):
        assert body_lines("a\nb\n", "    ") == ["    a", "    b"]

    def test_a_blank_line_is_not_indented(self):
        assert body_lines("a\n\nb\n", "    ") == ["    a", "", "    b"]

    def test_inner_indentation_survives(self):
        assert body_lines("a:\n  b: 1\n", "  ") == ["  a:", "    b: 1"]

    def test_empty_content(self):
        assert body_lines("", "") == []


class TestFenceLength:
    def test_the_floor_is_three(self):
        assert fence_length(["nothing"], "`", 3) == 3

    def test_one_longer_than_the_longest_line_initial_run(self):
        assert fence_length(["```bash", "x"], "`", 3) == 4

    def test_a_run_that_does_not_start_a_line_does_not_count(self):
        # Only a line-initial run can close a fence.
        assert fence_length(["use ``code`` inline"], "`", 3) == 3

    def test_an_indented_run_counts(self):
        assert fence_length(["    ````x"], "`", 3) == 5

    def test_the_authors_fence_is_never_shortened(self):
        assert fence_length(["x"], "`", 6) == 6

    def test_tildes_are_counted_separately(self):
        assert fence_length(["~~~~", "```"], "~", 3) == 5
        assert fence_length(["~~~~", "```"], "`", 3) == 4


class TestRender:
    def test_creates_a_fence_from_the_language(self):
        assert render("a: 1\n", fence=None, lang="yaml", indent="") == [
            "```yaml",
            "a: 1",
            "```",
        ]

    def test_keeps_an_existing_fence_line_verbatim(self):
        fence = Fence(indent="", char="`", length=3, info='yaml title="x"')

        rendered = render("a: 1\n", fence=fence, lang="ignored", indent="")

        assert rendered[0] == '```yaml title="x"'

    def test_lengthens_a_fence_the_body_would_close(self):
        fence = Fence(indent="", char="`", length=3, info="markdown")

        rendered = render(
            "```bash\nrun\n```\n",
            fence=fence,
            lang="markdown",
            indent="",
        )

        assert rendered[0] == "````markdown"
        assert rendered[-1] == "````"

    def test_a_created_fence_is_indented_with_the_annotation(self):
        rendered = render("a: 1\n", fence=None, lang="yaml", indent="    ")

        assert rendered == ["    ```yaml", "    a: 1", "    ```"]

    def test_an_existing_fence_lends_its_own_indentation(self):
        # The body has to sit under the fence that encloses it, whatever the
        # annotation above it happens to be indented by.
        fence = Fence(indent="  ", char="`", length=3, info="yaml")

        rendered = render("a: 1\n", fence=fence, lang="yaml", indent="")

        assert rendered == ["  ```yaml", "  a: 1", "  ```"]

    def test_a_tilde_fence_stays_a_tilde_fence(self):
        fence = Fence(indent="", char="~", length=3, info="yaml")

        rendered = render("a: 1\n", fence=fence, lang="yaml", indent="")

        assert rendered == ["~~~yaml", "a: 1", "~~~"]

    @pytest.mark.parametrize("indent", ["", "  ", "\t"])
    def test_an_empty_source_file_renders_an_empty_block(self, indent):
        rendered = render("", fence=None, lang="text", indent=indent)

        assert rendered == [f"{indent}```text", f"{indent}```"]
