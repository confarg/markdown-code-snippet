# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Keep code snippets in Markdown files up to date with their source files.

An annotation names a file, and optionally a symbol inside it; the tool writes
that file's current content into the code block below the annotation:

    <!-- snippet: examples/config.yaml -->
    <!-- snippet: src/app/models.py#User -->

Because the content is written into the document, the same file is correct on
GitHub and under mkdocs with nothing installed on either side. The cost is that
it has to be kept in step, which is what the ``markdown-code-snippet``
command-line tool and its ``--check`` mode are for.
"""

from markdown_code_snippet._process import (
    check_file,
    process_file,
    process_text,
)
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

__all__ = [
    "AbsolutePath",
    "AmbiguousSelector",
    "AnnotationError",
    "RootNotFound",
    "SelectorNotAScope",
    "SelectorNotFound",
    "SelectorUnsupported",
    "SnippetError",
    "SourceUnparsable",
    "SourceUnreadable",
    "TargetNotFound",
    "UnclosedBlock",
    "check_file",
    "process_file",
    "process_text",
]
