# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Whole-file extraction, and the reading rules every extractor shares."""

from __future__ import annotations

import pytest

from markdown_code_snippet._extract import extract
from markdown_code_snippet._extract._whole import extract_whole
from markdown_code_snippet.exceptions import SourceUnreadable, TargetNotFound


def test_returns_the_whole_file(write):
    source = write("config.yaml", "host: localhost\nport: 8080\n")

    assert extract_whole(source) == "host: localhost\nport: 8080\n"


def test_a_missing_file(tmp_path):
    with pytest.raises(TargetNotFound, match="no such file"):
        extract_whole(tmp_path / "absent.yaml")


def test_a_file_that_is_not_utf8(tmp_path):
    source = tmp_path / "binary.dat"
    source.write_bytes(b"\xff\xfe\x00\n")

    with pytest.raises(SourceUnreadable, match="not valid UTF-8"):
        extract_whole(source)


def test_a_directory_is_not_a_file(tmp_path):
    with pytest.raises(SourceUnreadable):
        extract_whole(tmp_path)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b"a\r\nb\r\n", "a\nb\n"),
        (b"a\rb\r", "a\nb\n"),
        (b"a\nb\n", "a\nb\n"),
    ],
)
def test_line_endings_are_normalized(tmp_path, raw, expected):
    source = tmp_path / "mixed.txt"
    source.write_bytes(raw)

    assert extract_whole(source) == expected


@pytest.fixture
def indented_fragment(tmp_path):
    """A file that is itself indented, written past the dedenting helper."""
    source = tmp_path / "fragment.yaml"
    source.write_bytes(b"    host: localhost\n    port: 8080\n")
    return source


def test_dedent_applies_to_a_whole_file_too(indented_fragment):
    assert extract(indented_fragment, None) == "host: localhost\nport: 8080\n"


def test_dedent_false_leaves_a_fragment_indented(indented_fragment):
    extracted = extract(indented_fragment, None, dedent=False)

    assert extracted == "    host: localhost\n    port: 8080\n"
