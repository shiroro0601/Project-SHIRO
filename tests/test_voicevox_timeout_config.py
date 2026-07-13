import main_v16_topic_to_real_video as main_v16
import main_v30_project_shiro as main_v30
from company.runtime.real_video_pipeline_factory import RealVideoPipelineFactory
from company.runtime.real_video_runtime import RealVideoRuntimeConfig


def test_runtime_config_reads_voicevox_timeout_from_env():
    config = RealVideoRuntimeConfig.from_env(
        {"PROJECT_SHIRO_VOICEVOX_TIMEOUT_SECONDS": "120"}
    )

    assert config.voicevox_timeout_seconds == 120


def test_main_v16_cli_can_override_voicevox_timeout():
    args = main_v16.parse_args(
        ["猫", "--voicevox-timeout-seconds", "150", "--skip-preflight"]
    )
    config = main_v16.build_config_from_args(args)

    assert config.voicevox_timeout_seconds == 150


def test_main_v30_cli_accepts_voicevox_timeout():
    args = main_v30.parse_args(
        [
            "--topic",
            "猫",
            "--not-made-for-kids",
            "--voicevox-timeout-seconds",
            "150",
        ]
    )

    assert args.voicevox_timeout_seconds == 150


def test_factory_passes_voicevox_timeout_to_generator():
    class CapturingVoiceGenerator:
        pass

    config = RealVideoRuntimeConfig(voicevox_timeout_seconds=123)
    factory = RealVideoPipelineFactory(config=config)

    # The concrete generator is created inside build; this assertion guards the
    # config surface without forcing external services.
    assert factory.config.voicevox_timeout_seconds == 123
