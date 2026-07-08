from company.artifacts.scene_asset import SceneAsset


class SceneVideoComposer:
    def compose(self, scene_assets: list[SceneAsset], output_path: str) -> str:
        raise NotImplementedError("SceneVideoComposer must implement compose().")


class FakeSceneVideoComposer:
    def __init__(self):
        self.received_scene_assets = []
        self.output_path = None

    def compose(self, scene_assets, output_path):
        self.received_scene_assets = scene_assets
        self.output_path = output_path
        return output_path
