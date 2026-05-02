from __future__ import annotations

from twitch_moderator.analyzers.factory import build_analyzer, build_semantic_analyzer
from twitch_moderator.buffer import MessageBuffer
from twitch_moderator.config import load_config
from twitch_moderator.decision_engine import DecisionEngine, DecisionPolicy
from twitch_moderator.executor import ActionExecutor
from twitch_moderator.irc import IRCConfig, TwitchIRCClient
from twitch_moderator.logging_config import configure_logging
from twitch_moderator.metrics import RuntimeMetrics
from twitch_moderator.runtime import build_runtime_context
from twitch_moderator.service import ModerationService
from twitch_moderator.twitch_api import TwitchAPIClient


def main() -> None:
    configure_logging()
    config = load_config()
    twitch_api = TwitchAPIClient(config.oauth_token)
    runtime = build_runtime_context(config, twitch_api)

    rule_based_analyzer = build_analyzer(config)
    semantic_analyzer = build_semantic_analyzer(config)
    decision_engine = DecisionEngine(
        DecisionPolicy(
            streamer_threshold=config.streamer_threshold,
            chatter_threshold=config.chatter_threshold,
            none_threshold=config.none_threshold,
            min_confidence=config.min_confidence,
        )
    )
    metrics = RuntimeMetrics()
    message_buffer = MessageBuffer(config.buffer_size)

    irc_client = TwitchIRCClient(
        IRCConfig(
            host=config.irc_host,
            port=config.irc_port,
            nickname=config.bot_username,
            oauth_token=config.oauth_token,
            channel=config.normalized_channel,
        )
    )
    executor = ActionExecutor(
        twitch_api=twitch_api,
        broadcaster_id=runtime.broadcaster.user_id,
        moderator_id=runtime.moderator.user_id,
    )
    service = ModerationService(
        rule_based_analyzer,
        message_buffer,
        executor,
        config,
        semantic_analyzer=semantic_analyzer,
        decision_engine=decision_engine,
        metrics=metrics,
    )

    irc_client.run_forever(service.handle_message)


if __name__ == "__main__":
    main()
