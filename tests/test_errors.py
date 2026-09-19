# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Every failure names the document and the annotation line it came from.

The reader of one of these messages has to go and edit one line of one file, so
each test asserts on the location as well as on the reason.
"""

from __future__ import annotations

import pytest

from markdown_code_snippet import process_file
from markdown_code_snippet.exceptions import (
    AbsolutePath,
    AmbiguousSelector,
    AnnotationError,
    RootNotFound,
    SelectorNotAScope,
    SelectorNotFound,
    SelectorUnsupported,
    SnippetError,
    SourceUnparsable,
    SourceUnreadable,
    TargetNotFound,
    UnclosedBlock,
)


@pytest.fixture
def project(root, write):
    """A project with one source file, and a place to put documents."""
    write("lib/config.yaml", "host: localhost\n")
    write("lib/app.py", "VALUE = 1\n")
    return root


def failing(project, body: str):
    """Write a document whose third line is an annotation, and process it."""
    path = project / "docs" / "doc.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"# Title\n\n{body}".encode())
    return path


@pytest.mark.parametrize(
    ("body", "expected", "reason"),
    [
        (
            "<!-- snippet: ../lib/absent.yaml -->\n",
            TargetNotFound,
            "no such file",
        ),
        (
            "<!-- snippet: ../lib -->\n",
            TargetNotFound,
            "no such file",
        ),
        (
            "<!-- snippet: /lib/app.py#missing -->\n",
            SelectorNotFound,
            "defines no 'missing'",
        ),
        (
            "<!-- snippet: /lib/app.py#VALUE.deeper -->\n",
            SelectorNotAScope,
            "not a class or a function",
        ),
        (
            "<!-- snippet: ../lib/config.yaml#server -->\n",
            SelectorUnsupported,
            "no selectors",
        ),
        (
            "<!-- snippet: C:/lib/app.py -->\n",
            AbsolutePath,
            "absolute path",
        ),
        (
            "<!-- snippet: -->\n",
            AnnotationError,
            "must name a file",
        ),
        (
            "<!-- snippet: ../lib/config.yaml --> and then prose\n",
            AnnotationError,
            "alone on its line",
        ),
        (
            "<!-- snippet: ../lib/config.yaml -->\n```yaml\nnever closed\n",
            UnclosedBlock,
            "never closed",
        ),
    ],
)
def test_is_reported_against_its_annotation(project, body, expected, reason):
    path = failing(project, body)

    with pytest.raises(expected) as raised:
        process_file(path)

    error = raised.value
    assert reason in str(error)
    assert error.document == path
    assert error.line == 3
    assert str(error).startswith(f"{path}:3: ")


def test_an_ambiguous_selector_lists_its_candidates(project, write):
    write(
        "lib/twice.py",
        """
        VALUE = 1
        VALUE = 2
        """,
    )
    path = failing(project, "<!-- snippet: ../lib/twice.py#VALUE -->\n")

    with pytest.raises(AmbiguousSelector) as raised:
        process_file(path)

    assert "lines 1, 2" in str(raised.value)
    assert str(raised.value).startswith(f"{path}:3: ")


def test_a_syntax_error_names_both_files(project, write):
    write("lib/broken.py", "def half(\n")
    path = failing(project, "<!-- snippet: ../lib/broken.py#half -->\n")

    with pytest.raises(SourceUnparsable) as raised:
        process_file(path)

    message = str(raised.value)
    assert f"{path}:3: " in message
    assert "broken.py at line 1" in message


def test_a_source_that_is_not_utf8(project):
    (project / "lib" / "binary.dat").write_bytes(b"\xff\xfe\x00\n")
    path = failing(project, "<!-- snippet: ../lib/binary.dat -->\n")

    with pytest.raises(SourceUnreadable, match="not valid UTF-8"):
        process_file(path)


def test_a_root_relative_path_with_no_root(tmp_path, monkeypatch):
    # The markers are removed rather than the tree being placed somewhere
    # unmarked: the walk has no upper bound, so on a machine whose home
    # directory is a checkout it would find that instead. See
    # docs-dev/architecture/07-limitations.md#root-discovery-has-no-upper-bound.
    monkeypatch.setattr("markdown_code_snippet._resolve.ROOT_MARKERS", ())
    path = tmp_path / "doc.md"
    path.write_bytes(b"<!-- snippet: /lib/app.py -->\n")

    with pytest.raises(RootNotFound, match="no project root") as raised:
        process_file(path, root=None)

    assert "--root" in str(raised.value)


def test_the_document_itself_may_be_missing(tmp_path):
    with pytest.raises(TargetNotFound):
        process_file(tmp_path / "absent.md")


def test_the_second_annotation_is_the_one_blamed(project):
    path = failing(
        project,
        "<!-- snippet: ../lib/config.yaml -->\n"
        "```yaml\n"
        "host: localhost\n"
        "```\n"
        "<!-- snippet: ../lib/absent.yaml -->\n",
    )

    with pytest.raises(TargetNotFound) as raised:
        process_file(path)

    assert raised.value.line == 7


class TestLocation:
    def test_an_unlocated_error_shows_only_its_reason(self):
        assert str(SnippetError("something went wrong")) == (
            "something went wrong"
        )

    def test_a_line_alone_is_shown(self):
        error = SnippetError("bad").located(4)

        assert str(error) == "line 4: bad"

    def test_the_innermost_line_wins(self):
        error = SnippetError("bad").located(4).located(9)

        assert error.line == 4

    def test_every_error_is_a_snippet_error(self):
        assert issubclass(AnnotationError, SnippetError)
        assert issubclass(TargetNotFound, SnippetError)
