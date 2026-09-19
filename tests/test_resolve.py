# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Path resolution and root discovery."""

from __future__ import annotations

import pytest

from markdown_code_snippet._resolve import ROOT_MARKERS, find_root, resolve
from markdown_code_snippet.exceptions import (
    AbsolutePath,
    RootNotFound,
    TargetNotFound,
)


class TestFindRoot:
    @pytest.mark.parametrize("marker", ROOT_MARKERS)
    def test_every_marker_is_recognized(self, tmp_path, marker):
        (tmp_path / marker).mkdir() if marker.startswith(
            ".",
        ) else (tmp_path / marker).write_bytes(b"")
        deep = tmp_path / "docs" / "guide"
        deep.mkdir(parents=True)

        assert find_root(deep) == tmp_path

    def test_the_directory_itself_counts(self, root):
        assert find_root(root) == root

    def test_the_nearest_marker_wins(self, tmp_path):
        (tmp_path / ".git").mkdir()
        package = tmp_path / "packages" / "inner"
        package.mkdir(parents=True)
        (package / "pyproject.toml").write_bytes(b"")

        assert find_root(package / "docs") == package

    def test_nothing_above_is_marked(self, tmp_path, monkeypatch):
        # Not expressible with real markers: the walk has no upper bound, so on
        # a machine whose home directory is itself a checkout it reaches that
        # instead of running out of ancestors. See 07-limitations.md.
        monkeypatch.setattr("markdown_code_snippet._resolve.ROOT_MARKERS", ())

        assert find_root(tmp_path) is None

    def test_the_walk_has_no_upper_bound(self, tmp_path):
        found = find_root(tmp_path)

        assert found is None or found in (tmp_path, *tmp_path.parents)


class TestResolve:
    def test_relative_to_the_document(self, root, write):
        target = write("docs/guide/config.yaml", "a: 1\n")
        document = root / "docs" / "guide" / "install.md"

        assert resolve("config.yaml", document=document, root=root) == target

    def test_up_and_across(self, root, write):
        target = write("docs/shared/a.yaml", "a: 1\n")
        document = root / "docs" / "guide" / "install.md"

        resolved = resolve("../shared/a.yaml", document=document, root=root)

        assert resolved == target

    def test_root_relative(self, root, write):
        target = write("src/app.py", "x = 1\n")
        document = root / "docs" / "guide" / "install.md"

        assert resolve("/src/app.py", document=document, root=root) == target

    def test_root_relative_ignores_extra_slashes(self, root, write):
        target = write("src/app.py", "x = 1\n")
        document = root / "docs" / "install.md"

        assert resolve("//src/app.py", document=document, root=root) == target

    def test_root_relative_with_no_root(self, tmp_path):
        with pytest.raises(RootNotFound, match="no project root"):
            resolve("/src/app.py", document=tmp_path / "a.md", root=None)

    @pytest.mark.parametrize(
        "path",
        ["C:/src/app.py", "C:\\src\\app.py", "\\\\server\\share\\a.py"],
    )
    def test_an_absolute_path_is_refused(self, tmp_path, path):
        # A path with a drive or a UNC prefix cannot survive a clone, and is
        # refused on every platform rather than only where it would resolve.
        with pytest.raises(AbsolutePath, match="absolute path"):
            resolve(path, document=tmp_path / "a.md", root=tmp_path)

    def test_a_missing_file(self, root):
        with pytest.raises(TargetNotFound, match="no such file"):
            resolve("absent.yaml", document=root / "a.md", root=root)

    def test_a_directory_is_not_a_target(self, root, write):
        write("lib/a.py", "x = 1\n")

        with pytest.raises(TargetNotFound):
            resolve("lib", document=root / "a.md", root=root)

    def test_a_relative_path_may_leave_the_root(self, tmp_path, write):
        # Deliberately allowed: a documentation subtree in a monorepo can point
        # at a sibling package. Only the /-prefixed form is anchored.
        target = write("outside.yaml", "a: 1\n")
        inner = tmp_path / "inner"
        inner.mkdir()
        (inner / "pyproject.toml").write_bytes(b"")

        resolved = resolve(
            "../outside.yaml",
            document=inner / "a.md",
            root=inner,
        )

        assert resolved == target
