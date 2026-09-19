# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The command line, which is what pre-commit runs."""

from __future__ import annotations

import pytest

from markdown_code_snippet._cli import CHANGED, FAILED, OK, documents, main


@pytest.fixture
def project(root, write):
    """A project holding a source file and two documents that quote it."""
    write("lib/config.yaml", "host: localhost\n")
    write("docs/first.md", "<!-- snippet: ../lib/config.yaml -->\n")
    write("docs/second.md", "# No annotations here\n")
    return root


def doc(project, name="first.md"):
    return str(project / "docs" / name)


class TestExitCodes:
    def test_nothing_to_do(self, project):
        main([doc(project)])

        assert main([doc(project)]) == OK

    def test_a_rewrite(self, project):
        assert main([doc(project)]) == CHANGED
        assert "host: localhost" in (project / "docs" / "first.md").read_text()

    def test_check_reports_without_writing(self, project):
        before = (project / "docs" / "first.md").read_bytes()

        assert main(["--check", doc(project)]) == CHANGED
        assert (project / "docs" / "first.md").read_bytes() == before

    def test_check_passes_once_the_file_is_current(self, project):
        main([doc(project)])

        assert main(["--check", doc(project)]) == OK

    def test_a_document_with_no_annotations(self, project):
        assert main([doc(project, "second.md")]) == OK

    def test_a_failure_outranks_a_rewrite(self, project, write):
        write("docs/broken.md", "<!-- snippet: ../lib/absent.yaml -->\n")

        assert main([str(project / "docs")]) == FAILED

    def test_a_failure_does_not_stop_the_other_documents(self, project, write):
        write("docs/broken.md", "<!-- snippet: ../lib/absent.yaml -->\n")

        main([str(project / "docs")])

        assert "host: localhost" in (project / "docs" / "first.md").read_text()


class TestOutput:
    def test_names_what_it_rewrote(self, project, capsys):
        main([doc(project)])

        assert "rewrote" in capsys.readouterr().out

    def test_names_what_is_out_of_date(self, project, capsys):
        main(["--check", doc(project)])

        assert "out of date" in capsys.readouterr().out

    def test_says_nothing_when_there_is_nothing_to_say(self, project, capsys):
        main([doc(project)])
        capsys.readouterr()

        main([doc(project)])

        assert capsys.readouterr().out == ""

    def test_a_failure_goes_to_stderr(self, project, write, capsys):
        write("docs/broken.md", "<!-- snippet: ../lib/absent.yaml -->\n")

        main([str(project / "docs" / "broken.md")])

        captured = capsys.readouterr()
        assert "no such file" in captured.err
        assert captured.out == ""


class TestRootOption:
    def test_overrides_discovery(self, tmp_path, write):
        write("elsewhere/lib/app.py", "VALUE = 2\n")
        write("project/pyproject.toml", "")
        document = write(
            "project/doc.md",
            "<!-- snippet: /lib/app.py#VALUE -->\n",
        )

        code = main(
            ["--root", str(tmp_path / "elsewhere"), str(document)],
        )

        assert code == CHANGED
        assert "VALUE = 2" in document.read_text()


class TestPathExpansion:
    def test_a_directory_contributes_every_markdown_file(self, project):
        found = documents([project / "docs"])

        assert [path.name for path in found] == ["first.md", "second.md"]

    def test_a_directory_is_searched_recursively(self, project, write):
        write("docs/deep/third.md", "# Third\n")

        found = documents([project / "docs"])

        assert [path.name for path in found] == [
            "third.md",
            "first.md",
            "second.md",
        ]

    def test_a_file_is_taken_as_given(self, project):
        path = project / "docs" / "first.md"

        assert documents([path]) == [path]

    def test_duplicates_are_dropped(self, project):
        # pre-commit can pass the same file more than once.
        path = project / "docs" / "first.md"

        assert documents([path, path, project / "docs"]) == [
            path,
            project / "docs" / "second.md",
        ]

    def test_a_missing_file_is_reported_not_skipped(self, project, capsys):
        assert main([str(project / "docs" / "absent.md")]) == FAILED
        assert "no such file" in capsys.readouterr().err
