import contextlib
import io
import json
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tools.codegrade.cli import EXIT_BELOW_THRESHOLD, EXIT_OK, EXIT_USAGE, main

CLEAN = """
export function Greeting({ name }: { name: string }) {
  return <p>Hello, {name}</p>;
}
"""

MESSY = """
var items = [];
export default function List() {
  console.log(items);
  debugger;
  return items.map((item, i) => <li key={i}><img src={item} /><button>x</button></li>);
}
"""


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.root = Path(self.workspace.name)
        self.addCleanup(self.workspace.cleanup)

    def write(self, name: str, code: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(code).lstrip(), encoding="utf-8")
        return path

    def test_clean_code_gets_a_score_but_no_rank(self) -> None:
        self.write("src/Greeting.tsx", CLEAN)

        code, out, _ = run_cli(str(self.root / "src"), "--root", str(self.root), "--no-hygiene")

        self.assertEqual(code, EXIT_OK)
        self.assertIn("CODE QUALITY", out)
        self.assertIn("Task not verified", out)
        self.assertNotIn("Excellent", out)
        self.assertIn("src/Greeting.tsx", out)

    def test_json_report_contains_scores_and_findings(self) -> None:
        self.write("src/List.jsx", MESSY)

        code, out, _ = run_cli(str(self.root), "--root", str(self.root), "--format", "json")

        self.assertEqual(code, EXIT_OK)
        report = json.loads(out)
        (file_report,) = report["quality"]["files"]
        rules = {item["rule"] for item in file_report["findings"]}
        self.assertTrue({"no-var", "no-debugger", "index-as-key", "img-alt"} <= rules)
        self.assertIsNone(report["grade"])
        self.assertEqual(report["verdict"], "quality_only")
        self.assertEqual(report["review"]["status"], "not_requested")
        self.assertEqual(report["scores"]["task"], None)
        self.assertLess(report["quality"]["hygiene_score"], 50)

    def test_fail_under_returns_non_zero(self) -> None:
        self.write("src/List.jsx", MESSY)

        code, _, err = run_cli(str(self.root), "--root", str(self.root), "--fail-under", "95")

        self.assertEqual(code, EXIT_BELOW_THRESHOLD)
        self.assertIn("below --fail-under 95", err)

    def test_dependencies_and_build_output_are_skipped(self) -> None:
        self.write("node_modules/lib/index.js", MESSY)
        self.write("dist/bundle.js", MESSY)
        self.write("src/types.d.ts", "declare const x: any;")
        self.write("src/Greeting.tsx", CLEAN)

        _, out, _ = run_cli(str(self.root), "--root", str(self.root), "--format", "json")

        paths = [item["path"] for item in json.loads(out)["quality"]["files"]]
        self.assertEqual(paths, ["src/Greeting.tsx"])

    def test_grades_a_zip_archive(self) -> None:
        archive_path = self.root / "project.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("project/src/List.jsx", textwrap.dedent(MESSY))

        code, out, _ = run_cli(str(archive_path), "--format", "json")

        self.assertEqual(code, EXIT_OK)
        report = json.loads(out)
        self.assertEqual(report["name"], "project.zip")
        self.assertEqual(report["source"], "archive")
        self.assertEqual([item["path"] for item in report["quality"]["files"]], ["src/List.jsx"])

    def test_task_without_ai_credentials_grades_quality_only(self) -> None:
        self.write("src/Greeting.tsx", CLEAN)
        env = {"CODEGRADE_AI_REVIEW": "off"}

        with mock.patch.dict("os.environ", env):
            code, out, _ = run_cli(
                str(self.root / "src"),
                "--root",
                str(self.root),
                "--no-hygiene",
                "--format",
                "json",
                "--task",
                "Greet the user by name.",
                "--explanation",
                "Renders a paragraph with the name.",
            )

        report = json.loads(out)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(report["review"]["status"], "unavailable")
        self.assertEqual(report["verdict"], "quality_only")
        self.assertIsNone(report["grade"])
        self.assertIsNone(report["overall_score"])
        self.assertIn("weren't verified", report["review"]["message"])

    def test_names_from_the_task_are_checked_without_ai(self) -> None:
        self.write("src/Greeting.tsx", CLEAN)
        env = {"CODEGRADE_AI_REVIEW": "off"}

        with mock.patch.dict("os.environ", env):
            _, out, _ = run_cli(
                str(self.root / "src"),
                "--root",
                str(self.root),
                "--no-hygiene",
                "--format",
                "json",
                "--task",
                "Build a component called Greeting and a helper called Farewell.",
                "--explanation",
                "`Greeting` renders a paragraph.",
            )

        checks = {
            (item["source"], item["name"]): item["status"] for item in json.loads(out)["checks"]
        }
        self.assertEqual(checks[("task", "Greeting")], "found")
        self.assertEqual(checks[("task", "Farewell")], "missing")
        self.assertEqual(checks[("explanation", "Greeting")], "found")

    def test_task_needs_an_explanation(self) -> None:
        self.write("src/Greeting.tsx", CLEAN)
        code, _, err = run_cli(str(self.root / "src"), "--task", "Greet the user.")
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("--explanation", err)

    def test_usage_errors(self) -> None:
        self.assertEqual(run_cli(str(self.root / "missing"))[0], EXIT_USAGE)
        self.write("notes.txt", "nothing to grade")
        self.assertEqual(run_cli(str(self.root), "--root", str(self.root))[0], EXIT_USAGE)
        self.write("broken.zip", "not really a zip")
        self.assertEqual(run_cli(str(self.root / "broken.zip"))[0], EXIT_USAGE)
