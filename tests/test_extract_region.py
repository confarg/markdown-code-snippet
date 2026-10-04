# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Extracting a span a source file marks out with comments."""

from __future__ import annotations

import pytest

from markdown_code_snippet._extract import extract
from markdown_code_snippet._extract._region import find_regions
from markdown_code_snippet.exceptions import (
    RegionMarkerError,
    SelectorNamesTwice,
    SelectorNotFound,
    SelectorUnsupported,
)


class TestMarkers:
    """Each comment syntax delimits a region; the markers are not in it."""

    @pytest.mark.parametrize(
        "source",
        [
            "# [snippet: a]\nkept\n# [/snippet]\n",
            "// [snippet: a]\nkept\n// [/snippet]\n",
            "; [snippet: a]\nkept\n; [/snippet]\n",
            "-- [snippet: a]\nkept\n-- [/snippet]\n",
            "<!-- [snippet: a] -->\nkept\n<!-- [/snippet] -->\n",
        ],
        ids=["hash", "slashes", "semicolon", "dashes", "html"],
    )
    def test_each_comment_syntax_opens_and_closes_a_region(self, write, source):
        path = write("config.txt", source)

        assert extract(path, "a") == "kept"

    def test_the_markers_are_stripped_from_the_region(self, write):
        path = write("app.py", "# [snippet: a]\nx = 1\ny = 2\n# [/snippet]\n")

        assert extract(path, "a") == "x = 1\ny = 2"

    def test_the_whole_file_keeps_its_markers(self, write):
        path = write("app.py", "# [snippet: a]\nx = 1\n# [/snippet]\n")

        assert extract(path, None) == "# [snippet: a]\nx = 1\n# [/snippet]\n"

    def test_a_marker_must_be_alone_on_its_line(self, write):
        path = write("app.py", "x = 1  # [snippet: a]\ny = 2\n")

        assert find_regions(path) == {}

    def test_a_marker_may_be_indented(self, tmp_path):
        # The write fixture dedents its text, which would strip the indentation
        # this test is about, so the bytes go straight to disk.
        path = tmp_path / "app.py"
        path.write_bytes(b"    # [snippet: a]\n    x = 1\n    # [/snippet]\n")

        assert extract(path, "a") == "x = 1"
        assert extract(path, "a", dedent=False) == "    x = 1"

    def test_a_region_is_dedented_like_any_other(self, write):
        path = write(
            "app.py",
            """
            def main():
                setup()
                # [snippet: body]
                value = compute()
                    # nested detail
                # [/snippet]
            """,
        )

        assert extract(path, "body") == "value = compute()\n    # nested detail"

    def test_an_empty_region_is_empty(self, write):
        path = write("app.py", "# [snippet: a]\n# [/snippet]\n")

        assert extract(path, "a") == ""


class TestRegionErrors:
    """A file whose markers do not balance is reported, never half-read."""

    @pytest.mark.parametrize(
        ("source", "reason"),
        [
            ("# [snippet: a]\nx\n", "never closed"),
            ("x\n# [/snippet]\n", "closes no region"),
            ("# [snippet: a]\n# [snippet: b]\n# [/snippet]\n", "cannot nest"),
            (
                (
                    "# [snippet: a]\na\n# [/snippet]\n"
                    "# [snippet: a]\n# [/snippet]\n"
                ),
                "already defined",
            ),
            ("# [snippet]\n# [/snippet]\n", "alone on its line"),
            ("# [snippet a]\n", "alone on its line"),
            ("# [snippet: a] trailing\n# [/snippet]\n", "alone on its line"),
            ("# [snippet: a]\n# [/snippet: a]\n", "alone on its line"),
            ("<!-- [snippet: a]\n", "alone on its line"),
        ],
        ids=[
            "never-closed",
            "close-without-open",
            "nested",
            "duplicate",
            "unnamed-start",
            "missing-colon",
            "trailing-text",
            "named-end",
            "unclosed-html",
        ],
    )
    def test_a_broken_region_is_an_error(self, write, source, reason):
        path = write("app.py", source)

        with pytest.raises(RegionMarkerError, match=reason):
            find_regions(path)

    def test_the_error_names_the_line_of_the_offending_marker(self, write):
        path = write("app.py", "x = 1\n# [/snippet]\n")

        with pytest.raises(RegionMarkerError, match=r"app\.py line 2:"):
            find_regions(path)

    def test_an_unclosed_region_is_reported_at_its_opening_line(self, write):
        path = write("app.py", "x = 1\n# [snippet: a]\ny = 2\n")

        with pytest.raises(RegionMarkerError, match=r"app\.py line 2:"):
            find_regions(path)


class TestDispatch:
    """A selector is answered by a region, a Python definition, or neither."""

    def test_a_region_in_a_file_that_is_not_python(self, write):
        path = write(
            "config.yaml",
            "# [snippet: server]\nhost: x\n# [/snippet]\n",
        )

        assert extract(path, "server") == "host: x"

    def test_an_unknown_name_lists_the_regions_that_exist(self, write):
        path = write(
            "config.yaml",
            "# [snippet: a]\n1\n# [/snippet]\n"
            "# [snippet: b]\n2\n# [/snippet]\n",
        )

        with pytest.raises(SelectorNotFound, match="available here: a, b"):
            extract(path, "c")

    def test_a_selector_on_a_file_with_no_regions_is_still_unsupported(
        self,
        write,
    ):
        path = write("config.yaml", "host: localhost\n")

        with pytest.raises(SelectorUnsupported, match="no selectors"):
            extract(path, "server")

    def test_a_region_in_python_is_found_by_name(self, write):
        path = write("app.py", "# [snippet: a]\nx = 1\n# [/snippet]\n")

        assert extract(path, "a") == "x = 1"

    def test_a_python_definition_is_found_when_no_region_matches(self, write):
        path = write(
            "app.py",
            "# [snippet: a]\nx = 1\n# [/snippet]\n\n"
            "def load():\n    return 2\n",
        )

        assert extract(path, "load") == "def load():\n    return 2"

    def test_a_name_that_is_both_a_region_and_a_definition_is_an_error(
        self,
        write,
    ):
        path = write(
            "app.py",
            "# [snippet: load]\nx = 1\n# [/snippet]\n\n"
            "def load():\n    return 2\n",
        )

        with pytest.raises(
            SelectorNamesTwice,
            match=r"region \(line 1\) and a definition \(line 5\)",
        ):
            extract(path, "load")

    def test_a_python_file_that_does_not_parse_still_yields_its_region(
        self,
        write,
    ):
        path = write("broken.py", "# [snippet: a]\nx = (\n# [/snippet]\n")

        assert extract(path, "a") == "x = ("

    def test_dedent_applies_to_a_region(self, write):
        path = write(
            "app.py",
            "class C:\n    # [snippet: m]\n    def f(self):\n"
            "        return 1\n    # [/snippet]\n",
        )

        assert extract(path, "m") == "def f(self):\n    return 1"
        assert (
            extract(path, "m", dedent=False)
            == "    def f(self):\n        return 1"
        )
