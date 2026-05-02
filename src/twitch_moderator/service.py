from __future__ import annotations

import logging

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.analyzers.semantic_base import SemanticAnalyzer, SemanticAnalyzerError
from twitch_moderator.buffer import MessageBuffer
from twitch_moderator.config import AppConfig
from twitch_moderator.decision_engine import DecisionEngine
from twitch_moderator.executor import ActionExecutor
from twitch_moderator.metrics import RuntimeMetrics
from twitch_moderator.models import ChatMessage, ModerationAction, SemanticAnalysisRequest
from twitch_moderator.twitch_api import TwitchAPIError


LOGGER = logging.getLogger(__name__)


class ModerationService:
    def __init__(
        self,
        rule_based_analyzer: Analyzer,
        message_buffer: MessageBuffer,
        executor: ActionExecutor,
        config: AppConfig,
        semantic_analyzer: SemanticAnalyzer | None = None,
        decision_engine: DecisionEngine | None = None,
        metrics: RuntimeMetrics | None = None,
    ) -> None:
        self._rule_based_analyzer = rule_based_analyzer
        self._semantic_analyzer = semantic_analyzer
        self._decision_engine = decision_engine
        self._message_buffer = message_buffer
        self._executor = executor
        self._config = config
        self._metrics = metrics

    def handle_message(self, message: ChatMessage) -> None:
        LOGGER.info(
            "Received message user=%s message=%r",
            message.username,
            message.message,
        )
        context = self._message_buffer.snapshot()
        rule_based_result = self._rule_based_analyzer.analyze(message, context)
        timed_out = False
        toxicity_for_metrics = 0.0
        target_for_metrics = None

        LOGGER.info(
            "Rule-based analysis user=%s toxic=%s confidence=%.2f reason=%s",
            message.username,
            rule_based_result.is_toxic,
            rule_based_result.confidence,
            rule_based_result.reason,
        )

        if rule_based_result.is_toxic:
            timed_out = self._execute_timeout(message, rule_based_result.reason)
            toxicity_for_metrics = 1.0
            LOGGER.info(
                "Final decision user=%s source=rule_based action=%s reason=%s",
                message.username,
                "timeout" if timed_out else "timeout_rejected",
                rule_based_result.reason,
            )
        elif self._semantic_analyzer is not None and self._decision_engine is not None:
            semantic_request = SemanticAnalysisRequest(
                current_message=message,
                context=context,
                streamer_identity=[self._config.normalized_channel],
                custom_rules=[],
            )
            try:
                semantic_result = self._semantic_analyzer.analyze(semantic_request)
            except SemanticAnalyzerError as exc:
                LOGGER.error(
                    "Semantic analysis failed for user=%s error=%s",
                    message.username,
                    exc,
                )
                LOGGER.info(
                    "Final decision user=%s source=semantic action=ignore reason=semantic_analysis_failed",
                    message.username,
                )
                self._finalize_message_metrics(
                    toxicity=0.0,
                    target=None,
                    timed_out=False,
                )
                self._message_buffer.add(message)
                return
            LOGGER.info(
                "Semantic analyzer result user=%s toxicity=%.2f target=%s confidence=%.2f reason=%s",
                message.username,
                semantic_result.toxicity,
                semantic_result.target,
                semantic_result.confidence,
                semantic_result.reason,
            )
            toxicity_for_metrics = semantic_result.toxicity
            target_for_metrics = semantic_result.target

            decision = self._decision_engine.decide(semantic_result)
            LOGGER.info(
                "Decision engine result user=%s should_timeout=%s reason=%s",
                message.username,
                decision.should_timeout,
                decision.reason,
            )

            if decision.should_timeout:
                timed_out = self._execute_timeout(message, decision.reason)
                LOGGER.info(
                    "Final decision user=%s source=semantic action=%s reason=%s",
                    message.username,
                    "timeout" if timed_out else "timeout_rejected",
                    decision.reason,
                )
            else:
                LOGGER.info(
                    "Final decision user=%s source=semantic action=ignore reason=%s",
                    message.username,
                    decision.reason,
                )
        else:
            LOGGER.info(
                "Final decision user=%s source=rule_based action=ignore reason=no_semantic_pipeline",
                message.username,
            )

        self._finalize_message_metrics(
            toxicity=toxicity_for_metrics,
            target=target_for_metrics,
            timed_out=timed_out,
        )
        self._message_buffer.add(message)

    def _execute_timeout(self, message: ChatMessage, reason: str) -> bool:
        action = ModerationAction(
            username=message.username,
            reason=reason,
            duration_seconds=self._config.timeout_duration,
        )
        try:
            self._executor.execute(action)
            return True
        except TwitchAPIError as exc:
            LOGGER.error(
                "Moderation action rejected for user=%s reason=%s error=%s",
                action.username,
                action.reason,
                exc,
            )
            return False
        except Exception:
            LOGGER.exception(
                "Unexpected moderation failure for user=%s reason=%s",
                action.username,
                action.reason,
            )
            return False

    def _finalize_message_metrics(self, toxicity: float, target: str | None, timed_out: bool) -> None:
        if self._metrics is None:
            return

        self._metrics.record_message(
            toxicity=toxicity,
            target=target,
            timed_out=timed_out,
        )
        if self._metrics.should_log_snapshot():
            snapshot = self._metrics.snapshot()
            LOGGER.info(
                "Metrics snapshot total_messages=%s average_toxicity=%.3f timeout_count=%s target_distribution=%s",
                snapshot.total_messages,
                snapshot.average_toxicity,
                snapshot.timeout_count,
                snapshot.target_distribution,
            )
