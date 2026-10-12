import unittest

from tools.codegrade.hygiene import ProjectSnapshot, check_hygiene, hygiene_score

REAL_README = "\n".join(f"Line {index} of real documentation" for index in range(40))


class HygieneTest(unittest.TestCase):
    def test_empty_project_scores_zero(self) -> None:
        checks = check_hygiene(ProjectSnapshot(frozenset({"src/app.js"})))
        self.assertEqual(hygiene_score(checks), 0)

    def test_well_kept_project_scores_full_marks(self) -> None:
        snapshot = ProjectSnapshot(
            frozenset(
                {
                    "README.md",
                    "src/App.test.tsx",
                    ".github/workflows/ci.yml",
                    "eslint.config.js",
                    ".prettierrc.json",
                    "tsconfig.json",
                    "LICENSE",
                    ".gitignore",
                    "package-lock.json",
                    ".editorconfig",
                }
            ),
            readme=REAL_README,
        )

        checks = check_hygiene(snapshot)

        self.assertEqual(hygiene_score(checks), 100)
        self.assertTrue(all(check.passed for check in checks))

    def test_boilerplate_readme_does_not_count(self) -> None:
        readme = (
            REAL_README + "\nThis template provides a minimal setup to get React working in Vite"
        )
        checks = {
            check.name: check for check in check_hygiene(ProjectSnapshot(frozenset(), readme))
        }
        self.assertFalse(checks["README"].passed)

    def test_config_patterns_only_match_at_the_project_root(self) -> None:
        nested = ProjectSnapshot(frozenset({"examples/tsconfig.json"}))
        self.assertFalse(nested.has("tsconfig.json"))
