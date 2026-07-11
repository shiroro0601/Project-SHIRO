from company.brain.provider import OllamaProvider
from company.core.ceo_decision import CEODecisionPolicy
from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.generators.stable_diffusion_generator import StableDiffusionGenerator
from company.generators.voicevox_generator import VOICEVOXGenerator
from company.runtime.real_video_runtime import (
    RealVideoPreflightChecker,
    RealVideoRuntimeConfig,
)
from company.video.scene_video_composer import MoviePySceneVideoComposer
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class NoOpPublisher:
    def generate(self, task) -> dict:
        input_data = getattr(task, "input_data", {}) or {}
        return {
            "status": "dry_run",
            "platform": "none",
            "video_path": input_data.get("video_path", ""),
            "metadata": input_data.get("metadata", {}),
        }


class OutputPathSceneVideoComposer:
    def __init__(self, composer, output_path: str):
        self.composer = composer
        self.output_path = output_path

    def compose(self, scene_assets, output_path: str) -> str:
        return self.composer.compose(scene_assets, self.output_path)


class RealVideoPipelineFactory:
    def __init__(
        self,
        config: RealVideoRuntimeConfig | None = None,
        provider=None,
        image_generator=None,
        voice_generator=None,
        scene_video_composer=None,
        publisher=None,
        ceo_decision_policy=None,
    ):
        self.config = config or RealVideoRuntimeConfig.from_env()
        self.provider = provider
        self.image_generator = image_generator
        self.voice_generator = voice_generator
        self.scene_video_composer = scene_video_composer
        self.publisher = publisher
        self.ceo_decision_policy = ceo_decision_policy

    def build(self) -> FullAutoVideoPipeline:
        provider = self.provider or OllamaProvider(
            model=self.config.ollama_model,
            base_url=self.config.ollama_base_url,
            timeout=self.config.request_timeout,
        )
        composer = self.scene_video_composer or MoviePySceneVideoComposer(
            fps=self.config.fps
        )
        return FullAutoVideoPipeline(
            researcher=ResearchRole(provider=provider),
            writer=WriterRole(provider=provider),
            reviewer=ReviewerRole(provider=provider),
            image_generator=self.image_generator
            or StableDiffusionGenerator(
                base_url=self.config.stable_diffusion_base_url,
                output_dir=self.config.images_dir,
                timeout=self.config.request_timeout,
            ),
            voice_generator=self.voice_generator
            or VOICEVOXGenerator(
                base_url=self.config.voicevox_base_url,
                output_dir=self.config.voices_dir,
                speaker=self.config.voicevox_speaker_id,
                timeout=self.config.request_timeout,
            ),
            scene_video_composer=OutputPathSceneVideoComposer(
                composer,
                self.config.final_video_path,
            ),
            publisher=self.publisher or NoOpPublisher(),
            ceo_decision_policy=self.ceo_decision_policy or CEODecisionPolicy(),
            stop_on_ceo_stop=False,
            require_human_approval_on_stop=False,
        )

    def create_preflight_checker(self) -> RealVideoPreflightChecker:
        return RealVideoPreflightChecker(self.config)
