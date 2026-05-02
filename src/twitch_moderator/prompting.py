from __future__ import annotations

from pathlib import Path

from twitch_moderator.models import SemanticAnalysisRequest


DEFAULT_PROMPT_PATH = Path("prompts/semantic_analyzer_prompt.txt")


def load_prompt_template(prompt_path: str | Path = DEFAULT_PROMPT_PATH) -> str:
    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Semantic prompt file not found: {path}. "
            "Create the file or update the configured prompt path."
        )

    return path.read_text(encoding="utf-8")


def render_semantic_prompt(template: str, request: SemanticAnalysisRequest) -> str:
    return template.format(
        streamer_identity=_format_streamer_identity(request.streamer_identity),
        custom_rules=_format_custom_rules(request.custom_rules),
        current_username=request.current_message.username,
        current_message=request.current_message.message,
        context_block=_format_context(request.context),
    )


def _format_streamer_identity(streamer_identity: list[str]) -> str:
    if not streamer_identity:
        return "- none"
    return "\n".join(f"- {identity}" for identity in streamer_identity)


def _format_custom_rules(custom_rules: list[str]) -> str:
    if not custom_rules:
        return "- none"
    return "\n".join(f"- {rule}" for rule in custom_rules)


def _format_context(context: list) -> str:
    if not context:
        return "- none"
    return "\n".join(f"- {message.username}: {message.message}" for message in context)
