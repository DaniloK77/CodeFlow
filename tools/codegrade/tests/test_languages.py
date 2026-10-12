"""The input gate: what gets graded, as which language, and what is turned away."""

from __future__ import annotations

import contextlib
import time

import pytest

from tools.codegrade.languages import UngradableInputError, detect_extension, ensure_gradable

from .helpers import make_source

SUPPORTED = [
    (".py", "def add(first, second):\n    return first + second\n"),
    (".py", "import os\nprint(os.getcwd())\n"),
    (".py", "def add(first, second)\n    return first + second\nimport os\nprint(add(1, 2))\n"),
    (".js", "export function sum(first, second) {\n  return first + second;\n}\n"),
    (".js", "function add(first, second {\n  return first + ;\n}\nadd(1, 2);\n"),
    (".jsx", "export const Title = () => <h1 className='title'>{text}</h1>;"),
    (".ts", "interface User { id: string }\nexport const idOf = (user: User): string => user.id;"),
    (".ts", "const cast = <T>(value: unknown) => value as T;"),
    (".tsx", "export function Name({ id }: { id: string }) { return <p>{id}</p>; }"),
]

REJECTED = [
    ("not_code", "Hello, this is not code at all. Just a sentence about my weekend plans."),
    ("not_code", "asdf qwer zxcv 1234 !!! ??? lorem ipsum dolor"),
    ("not_code", "apple\nbanana\ncherry\ndate"),
    ("not_code", "42"),
    ("not_code", '{ "name": "config", "version": 2 }'),
    (
        "unsupported_language",
        "public class Main {\n  public static void main(String[] args) {\n"
        '    System.out.println("Hi");\n  }\n}\n',
    ),
    ("unsupported_language", "SELECT * FROM users WHERE id = 1;"),
    ("unsupported_language", "<!DOCTYPE html>\n<html><body><div>hi</div></body></html>"),
    ("unsupported_language", "<html><body><div>hi</div></body></html>"),
    ("unsupported_language", ".card {\n  color: red;\n  padding: 4px;\n}\n"),
    ("unsupported_language", 'package main\nimport "fmt"\nfunc main() {\n  fmt.Println("hi")\n}\n'),
    ("unsupported_language", "#include <stdio.h>\nint main() { return 0; }"),
    ("unsupported_language", 'fn main() {\n    println!("hi");\n}'),
    ("unsupported_language", "<?php\n$name = 'x';\necho $name;"),
    ("unsupported_language", "#!/bin/bash\nset -e\nnpm run build\n"),
    ("unsupported_language", 'def greet(name)\n  puts "hi #{name}"\nend\n'),
]


@pytest.mark.parametrize(("extension", "code"), SUPPORTED)
def test_detects_supported_languages(extension: str, code: str) -> None:
    assert detect_extension(code) == extension


@pytest.mark.parametrize(("reason", "code"), REJECTED)
def test_turns_away_everything_else(reason: str, code: str) -> None:
    with pytest.raises(UngradableInputError) as rejection:
        detect_extension(code)
    assert rejection.value.code == reason


def test_typescript_that_resembles_other_languages_is_still_typescript() -> None:
    code = """
        interface Theme {
          color: string;
          padding: number;
        }
        const $button = document.querySelector<HTMLButtonElement>("button");
        export const theme: Theme = { color: "red", padding: 4 };
    """
    assert detect_extension(code) == ".ts"


@pytest.mark.parametrize("code", ["const total = 5;", "x = 1", "import os"])
def test_one_or_two_lines_are_too_little_to_grade(code: str) -> None:
    source = make_source(code, f"snippet{detect_extension(code)}")
    with pytest.raises(UngradableInputError) as rejection:
        ensure_gradable(source)
    assert rejection.value.code == "too_little_code"


def test_comments_do_not_count_towards_the_minimum() -> None:
    source = make_source("// one\n// two\n// three\nconst total = 5;\n", "snippet.js")
    with pytest.raises(UngradableInputError):
        ensure_gradable(source)


def test_a_file_that_is_mostly_not_its_language_is_rejected() -> None:
    source = make_source("This is my homework.\nI did it yesterday.\nPlease grade it.\n", "a.js")
    with pytest.raises(UngradableInputError) as rejection:
        ensure_gradable(source)
    assert rejection.value.code == "not_code"


def test_real_code_passes_the_gate() -> None:
    ensure_gradable(make_source("def add(a, b):\n    total = a + b\n    return total\n", "a.py"))


@pytest.mark.parametrize(
    "payload",
    ["\n" * 150_000, "def f(:\n" * 20_000, "{ a: b;\n" * 20_000, "word " * 40_000],
    ids=["blank lines", "broken defs", "css-like", "prose"],
)
def test_hostile_input_is_classified_quickly(payload: str) -> None:
    started = time.perf_counter()
    with contextlib.suppress(UngradableInputError):
        detect_extension(payload)
    assert time.perf_counter() - started < 3
