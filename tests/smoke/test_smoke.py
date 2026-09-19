# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Run the smoke corpus: one annotated document and its expected result.

The corpus is the specification by example. A case is a folder under ``cases/``
holding an ``input.md`` and the ``expected.md`` it must turn into; the documents
point at the shared source tree in ``tree/``, which is copied into a temporary
directory so a run never writes inside the repository.

Each case is asserted four ways: processing the input yields the expected
document, processing the expected document changes nothing, processing the input
twice changes nothing after the first pass, and the return value says whether
anything was written. The middle two are the idempotency invariant the
pre-commit hook rests on.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from markdown_code_snippet import process_file

HERE = Path(__file__).parent
CASES = sorted(p.name for p in (HERE / "cases").iterdir() if p.is_dir())


def read(path: Path) -> str:
    """Return a file's text, normalized whatever git checked out."""
    raw = path.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n").replace("\r", "\n")


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Copy the source tree into a temporary project, and return its root."""
    shutil.copytree(HERE / "tree", tmp_path, dirs_exist_ok=True)
    # The root marker is written rather than committed: a second pyproject.toml
    # inside the repository confuses tools that discover configuration by
    # walking upwards.
    (tmp_path / "pyproject.toml").write_bytes(b"")
    return tmp_path


def write_doc(tree: Path, text: str) -> Path:
    """Place a document where every case was written to expect it."""
    doc = tree / "docs" / "doc.md"
    doc.write_bytes(text.encode("utf-8"))
    return doc


@pytest.mark.parametrize("case", CASES)
def test_input_becomes_expected(case: str, tree: Path) -> None:
    expected = read(HERE / "cases" / case / "expected.md")
    doc = write_doc(tree, read(HERE / "cases" / case / "input.md"))

    process_file(doc)

    assert read(doc) == expected


@pytest.mark.parametrize("case", CASES)
def test_expected_is_a_fixed_point(case: str, tree: Path) -> None:
    expected = read(HERE / "cases" / case / "expected.md")
    doc = write_doc(tree, expected)

    changed = process_file(doc)

    assert read(doc) == expected
    assert changed is False


@pytest.mark.parametrize("case", CASES)
def test_second_pass_changes_nothing(case: str, tree: Path) -> None:
    doc = write_doc(tree, read(HERE / "cases" / case / "input.md"))
    process_file(doc)

    assert process_file(doc) is False


@pytest.mark.parametrize("case", CASES)
def test_reports_whether_it_changed_anything(case: str, tree: Path) -> None:
    source = read(HERE / "cases" / case / "input.md")
    expected = read(HERE / "cases" / case / "expected.md")
    doc = write_doc(tree, source)

    assert process_file(doc) is (source != expected)
