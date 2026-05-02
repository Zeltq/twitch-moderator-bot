import unittest
from pathlib import Path

from twitch_moderator.models import ChatMessage, SemanticAnalysisRequest
from twitch_moderator.prompting import load_prompt_template, render_semantic_prompt


class PromptingTests(unittest.TestCase):
    def test_load_prompt_template_reads_file(self) -> None:
        prompt_path = Path("tests/test_prompt_template.txt")
        prompt_path.write_text("Hello {streamer_identity}", encoding="utf-8")
        try:
            self.assertEqual(load_prompt_template(prompt_path), "Hello {streamer_identity}")
        finally:
            if prompt_path.exists():
                prompt_path.unlink()

    def test_load_prompt_template_raises_clear_error_for_missing_file(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Semantic prompt file not found"):
            load_prompt_template("tests/does_not_exist_prompt.txt")

    def test_render_semantic_prompt_injects_request_fields(self) -> None:
        template = (
            "Streamer:\n{streamer_identity}\n"
            "Rules:\n{custom_rules}\n"
            "Message: {current_username} -> {current_message}\n"
            "Context:\n{context_block}"
        )
        request = SemanticAnalysisRequest(
            current_message=ChatMessage(username="user1", message="hello there"),
            context=[ChatMessage(username="user2", message="previous line")],
            streamer_identity=["zeltq", "Леша"],
            custom_rules=["Do not insult the streamer"],
        )

        rendered = render_semantic_prompt(template, request)

        self.assertIn("- zeltq", rendered)
        self.assertIn("- Леша", rendered)
        self.assertIn("- Do not insult the streamer", rendered)
        self.assertIn("Message: user1 -> hello there", rendered)
        self.assertIn("- user2: previous line", rendered)


if __name__ == "__main__":
    unittest.main()
