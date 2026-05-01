from __future__ import annotations

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.analyzers.rule_based import RuleBasedAnalyzer
from twitch_moderator.config import AppConfig


def build_analyzer(config: AppConfig) -> Analyzer:
    if config.analyzer_type == "rule_based":
        return RuleBasedAnalyzer(config.blacklist)

    raise ValueError(f"Unsupported analyzer type: {config.analyzer_type}")
