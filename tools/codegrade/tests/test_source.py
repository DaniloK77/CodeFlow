"""Source files: language by extension, which lines are code, and what counts as a test."""

from __future__ import annotations

import pytest

from tools.codegrade.source import SourceFile, is_test_file

from .helpers import make_source


def test_javascript_comments_and_string_bodies_are_not_code_lines() -> None:
    source = make_source(
        """
        // a comment
        const first = 1;

        /* a block
           comment */
        const text = `
          only text here
        `;
        """,
        "sample.js",
    )
    assert sorted(source.code_line_numbers) == [2, 6, 8]
    assert source.code_lines == 3


def test_python_docstrings_and_comments_are_not_code_lines() -> None:
    source = make_source(
        '''
        """Module docstring."""

        # a comment
        def run() -> int:
            """Docstring."""
            return 1  # trailing comment
        ''',
        "sample.py",
    )
    assert sorted(source.code_line_numbers) == [4, 6]


def test_python_that_does_not_tokenize_still_counts_lines() -> None:
    source = make_source("def broken(:\n    return (1\n# note\n", "broken.py")
    assert source.code_lines == 2


@pytest.mark.parametrize(
    ("name", "language"),
    [("a.ts", "typescript"), ("a.tsx", "typescript"), ("a.mjs", "javascript"), ("a.py", "python")],
)
def test_language_follows_the_extension(name: str, language: str) -> None:
    source = SourceFile.from_text(name, "")
    assert source is not None
    assert source.language == language


def test_unsupported_files_are_not_sources() -> None:
    assert SourceFile.from_text("styles.css", "a { color: red; }") is None


def test_ts_files_parse_generics_that_tsx_would_read_as_jsx() -> None:
    source = make_source("const cast = <T>(value: unknown) => value as T;", "cast.ts")
    assert not source.tree.root_node.has_error


@pytest.mark.parametrize(
    "name",
    [
        "src/App.test.tsx",
        "lib/format.spec.js",
        "tests/helpers.py",
        "test_cli.py",
        "api/conftest.py",
    ],
)
def test_recognises_test_files(name: str) -> None:
    assert is_test_file(name)


@pytest.mark.parametrize("name", ["src/App.tsx", "contest.py", "latest/app.py", "testimonials.ts"])
def test_production_files_are_not_tests(name: str) -> None:
    assert not is_test_file(name)
