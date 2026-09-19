# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Guessing the language for a fence the tool has to create."""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_code_snippet._lang import FALLBACK, language_for


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("config.yaml", "yaml"),
        ("config.yml", "yaml"),
        ("app.py", "python"),
        ("app.pyi", "python"),
        ("pyproject.toml", "toml"),
        ("data.json", "json"),
        ("README.md", "markdown"),
        ("run.sh", "bash"),
        ("build.ps1", "powershell"),
        ("notes.txt", "text"),
        ("Dockerfile", "dockerfile"),
        ("Makefile", "makefile"),
        (".gitignore", "gitignore"),
    ],
)
def test_known_names(name, expected):
    assert language_for(Path("some/dir") / name) == expected


def test_the_suffix_is_matched_case_insensitively():
    assert language_for(Path("CONFIG.YAML")) == "yaml"


def test_a_name_beats_a_suffix():
    # CMakeLists.txt is CMake, not the plain text its suffix claims.
    assert language_for(Path("CMakeLists.txt")) == "cmake"


@pytest.mark.parametrize("name", ["mystery.qqq", "no-extension", "a."])
def test_anything_unknown_falls_back(name):
    assert language_for(Path(name)) == FALLBACK
