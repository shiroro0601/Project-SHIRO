import main_v16_topic_to_real_video as main_v16


def test_parse_args_accepts_topic_and_options():
    args = main_v16.parse_args(
        [
            "猫の意外な雑学",
            "--output-root",
            "outputs/custom",
            "--ollama-model",
            "llama-test",
            "--voicevox-speaker-id",
            "2",
            "--skip-preflight",
            "--no-report",
            "--no-memory",
        ]
    )

    assert args.topic == "猫の意外な雑学"
    assert args.output_root == "outputs/custom"
    assert args.ollama_model == "llama-test"
    assert args.voicevox_speaker_id == 2
    assert args.skip_preflight is True
    assert args.no_report is True
    assert args.no_memory is True


def test_build_config_from_args_applies_cli_values():
    args = main_v16.parse_args(
        [
            "猫の意外な雑学",
            "--output-root",
            "outputs/custom",
            "--ollama-model",
            "llama-test",
            "--voicevox-speaker-id",
            "4",
        ]
    )

    config = main_v16.build_config_from_args(args)

    assert config.output_root == "outputs/custom"
    assert config.ollama_model == "llama-test"
    assert config.voicevox_speaker_id == 4


def test_main_returns_zero_on_success(monkeypatch, capsys):
    def fake_run_topic_to_real_video(*args, **kwargs):
        return {
            "topic": "猫の意外な雑学",
            "video_path": "final_video.mp4",
            "video_validation": {"size_bytes": 123},
            "report_path": "report.json",
            "memory_record": {"summary": "saved"},
        }

    monkeypatch.setattr(
        main_v16,
        "run_topic_to_real_video",
        fake_run_topic_to_real_video,
    )

    exit_code = main_v16.main(["猫の意外な雑学"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "final_video.mp4" in captured.out
    assert "report.json" in captured.out


def test_main_returns_one_on_runtime_error(monkeypatch, capsys):
    def fake_run_topic_to_real_video(*args, **kwargs):
        raise RuntimeError("service down")

    monkeypatch.setattr(
        main_v16,
        "run_topic_to_real_video",
        fake_run_topic_to_real_video,
    )

    exit_code = main_v16.main(["猫の意外な雑学"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "service down" in captured.out
