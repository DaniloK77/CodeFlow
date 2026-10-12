"""Keeps the web app's copy of engine vocabulary (rule ids, dimensions) in sync."""

import re
import unittest
from pathlib import Path

from tools.codegrade.models import RULE_DIMENSIONS, Dimension

WEB_ANALYZER = Path(__file__).resolve().parents[3] / "src" / "features" / "analyzer"


class WebContractTest(unittest.TestCase):
    def test_every_rule_is_explained_in_the_ui(self) -> None:
        source = (WEB_ANALYZER / "ruleDocs.ts").read_text(encoding="utf-8")
        documented = dict(
            re.findall(
                r'^  "?([a-z-]+)"?: \{\n\s+title: .*\n\s+why: .*\n\s+dimension: "(\w+)"',
                source,
                re.MULTILINE,
            )
        )
        expected = {rule: dimension.value for rule, dimension in RULE_DIMENSIONS.items()}
        self.assertEqual(documented, expected)

    def test_dimensions_match_the_ui_schema(self) -> None:
        source = (WEB_ANALYZER / "dimensions.ts").read_text(encoding="utf-8")
        block = re.search(r"export const DIMENSIONS = \[(.*?)\]", source, re.DOTALL)
        assert block is not None
        self.assertEqual(
            re.findall(r'"(\w+)"', block.group(1)), [dimension.value for dimension in Dimension]
        )
