from __future__ import annotations

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.analyzers.rule_based import RuleBasedAnalyzer
from twitch_moderator.analyzers.semantic_adapter import SemanticAnalyzerAdapter
from twitch_moderator.analyzers.semantic_base import SemanticAnalyzer
from twitch_moderator.analyzers.semantic_stub import LLMStubAnalyzer
from twitch_moderator.config import AppConfig
from twitch_moderator.prompting import load_prompt_template


def build_analyzer(config: AppConfig) -> Analyzer:
    if config.analyzer_type == "rule_based":
        return RuleBasedAnalyzer(config.blacklist)

    raise ValueError(f"Unsupported analyzer type: {config.analyzer_type}")


def build_semantic_analyzer(config: AppConfig) -> SemanticAnalyzer:
    prompt_template = load_prompt_template()
    return LLMStubAnalyzer(
        prompt_template=prompt_template,
        timeout_seconds=config.llm_timeout_seconds,
        retry_count=config.llm_retry_count,
    )


def build_semantic_analyzer_adapter(config: AppConfig) -> Analyzer:
    return SemanticAnalyzerAdapter(
        semantic_analyzer=build_semantic_analyzer(config),
        streamer_identity=[config.normalized_channel],
        custom_rules=[],
    )
