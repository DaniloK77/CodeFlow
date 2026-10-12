import importlib.util
import json
import unittest
from contextlib import contextmanager
from types import SimpleNamespace

from tools.codegrade.ai_review import (
    DEFAULT_MODEL,
    REVIEW_SCHEMA,
    ClaudeReviewer,
    build_prompt,
    credentials_available,
    reviewer_from_env,
    select_sources,
)
from tools.codegrade.assignment import ReviewError

from .helpers import make_source

HAS_SDK = importlib.util.find_spec("anthropic") is not None
if HAS_SDK:
    import anthropic
    import httpx2
VALID_ANSWER = {
    "summary": "Correct and readable.",
    "requirements": [{"requirement": "Adds numbers", "status": "met", "evidence": "add.py:1"}],
    "bugs": [],
    "explanation": {
        "accuracy": "accurate",
        "completeness": "complete",
        "clarity": "clear",
        "feedback": "Clear.",
    },
    "strengths": ["Tiny"],
    "improvements": [],
}


def fake_message(text: str | None, stop_reason: str = "end_turn") -> SimpleNamespace:
    content = [] if text is None else [SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(content=content, stop_reason=stop_reason, model="claude-opus-5-5")


SOURCES = (make_source("def add(a: int, b: int) -> int:\n    return a + b\n", "add.py"),)


class FakeClient:
    """Mimics `client.beta.messages.stream(...)` and records the request."""

    def __init__(self, message: SimpleNamespace) -> None:
        self.message = message
        self.requests: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    @contextmanager
    def _stream(self, **request):
        self.requests.append(request)
        yield SimpleNamespace(get_final_message=lambda: self.message)


class PromptTest(unittest.TestCase):
    def test_wraps_inputs_in_tags_with_line_numbers(self) -> None:
        source = make_source("def add(a, b):\n    return a + b\n", "add.py")

        prompt = build_prompt("Add two numbers.", "I return a + b.", select_sources([source]))

        self.assertIn("<task>\nAdd two numbers.\n</task>", prompt)
        self.assertIn("<explanation>\nI return a + b.\n</explanation>", prompt)
        self.assertIn('<file path="add.py">\n1 | def add(a, b):\n2 |     return a + b', prompt)

    def test_lists_files_that_did_not_fit(self) -> None:
        small = make_source("export const a = 1;\n", "a.ts")
        large = make_source("export const b = 2;\n" * 50, "b.ts")
        test = make_source("it('works', () => {});\n", "a.test.ts")

        selection = select_sources([test, large, small], budget=100)

        self.assertEqual([source.label for source in selection.included], ["a.ts", "a.test.ts"])
        self.assertEqual(selection.omitted, ("b.ts",))
        self.assertIn(
            '<omitted reason="size limit">b.ts</omitted>', build_prompt("t", "e", selection)
        )


@unittest.skipUnless(HAS_SDK, "the optional anthropic package is not installed")
class ClaudeReviewerTest(unittest.TestCase):
    def test_requests_structured_output_with_fallbacks(self) -> None:
        client = FakeClient(fake_message(json.dumps(VALID_ANSWER)))

        review = ClaudeReviewer(client=client).review("Add numbers.", "Returns a + b.", SOURCES)

        (request,) = client.requests
        self.assertEqual(request["model"], DEFAULT_MODEL)
        self.assertEqual(request["fallbacks"], "default")
        self.assertEqual(request["thinking"], {"type": "adaptive"})
        self.assertEqual(request["output_config"]["format"]["schema"], REVIEW_SCHEMA)
        self.assertEqual(review.requirements[0].status, "met")
        self.assertEqual((review.model, review.files_reviewed), ("claude-opus-5-5", 1))

    def test_turns_unusable_answers_into_review_errors(self) -> None:
        cases = {
            "declined": fake_message(None, stop_reason="refusal"),
            "cut short": fake_message("{", stop_reason="max_tokens"),
            "empty answer": fake_message(None),
            "malformed JSON": fake_message("not json"),
        }
        for expected, message in cases.items():
            with self.subTest(case=expected), self.assertRaisesRegex(ReviewError, expected):
                ClaudeReviewer(client=FakeClient(message)).review("t", "e", SOURCES)

    def test_maps_connection_failures_to_a_friendly_message(self) -> None:
        def unreachable(**_request):
            raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api"))

        client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(stream=unreachable)))
        with self.assertRaisesRegex(ReviewError, "couldn't be reached"):
            ClaudeReviewer(client=client).review("t", "e", SOURCES)


class ConfigurationTest(unittest.TestCase):
    def test_credentials_come_from_the_environment(self) -> None:
        self.assertTrue(
            credentials_available({"ANTHROPIC_API_KEY": "sk-test", "XDG_CONFIG_HOME": "/nowhere"})
        )
        self.assertFalse(credentials_available({"XDG_CONFIG_HOME": "/nowhere"}))

    def test_reviewer_can_be_switched_off_or_configured(self) -> None:
        env = {"ANTHROPIC_API_KEY": "sk-test", "XDG_CONFIG_HOME": "/nowhere"}
        self.assertIsNone(reviewer_from_env({**env, "CODEGRADE_AI_REVIEW": "off"}))
        self.assertIsNone(reviewer_from_env({"XDG_CONFIG_HOME": "/nowhere"}))
        if HAS_SDK:
            reviewer = reviewer_from_env({**env, "CODEGRADE_AI_MODEL": "claude-sonnet-5-5"})
            self.assertEqual(reviewer.model if reviewer else None, "claude-sonnet-5-5")
