from company.runtime.real_video_pipeline_factory import (
    NoOpPublisher,
    RealVideoPipelineFactory,
)
from company.runtime.real_video_runtime import RealVideoRuntimeConfig


class FakeProvider:
    def generate(self, prompt):
        return "generated"


class FakeImageGenerator:
    pass


class FakeVoiceGenerator:
    pass


class FakeComposer:
    def __init__(self):
        self.output_path = None

    def compose(self, scene_assets, output_path):
        self.output_path = output_path
        return output_path


def test_factory_injects_real_ai_roles_and_media_components(tmp_path):
    provider = FakeProvider()
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    composer = FakeComposer()
    config = RealVideoRuntimeConfig(output_root=str(tmp_path))

    company = RealVideoPipelineFactory(
        config=config,
        provider=provider,
        image_generator=image_generator,
        voice_generator=voice_generator,
        scene_video_composer=composer,
        publisher=NoOpPublisher(),
    ).build()

    assert company.researcher.provider is provider
    assert company.writer.provider is provider
    assert company.reviewer.provider is provider
    assert company.image_generator is image_generator
    assert company.voice_generator is voice_generator
    assert company.publisher.generate(None)["status"] == "dry_run"


def test_factory_routes_scene_video_to_config_output_path(tmp_path):
    composer = FakeComposer()
    config = RealVideoRuntimeConfig(output_root=str(tmp_path))
    company = RealVideoPipelineFactory(
        config=config,
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=composer,
    ).build()

    video_path = company.scene_video_composer.compose([], "ignored.mp4")

    assert video_path == config.final_video_path
    assert composer.output_path == config.final_video_path


def test_factory_creates_matching_preflight_checker(tmp_path):
    config = RealVideoRuntimeConfig(output_root=str(tmp_path))
    checker = RealVideoPipelineFactory(config=config).create_preflight_checker()

    assert checker.config is config
