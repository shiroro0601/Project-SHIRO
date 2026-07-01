from company.core.artifact import ArtifactFactory, ArtifactType


def test_artifact_factory_creates_artifact():
    artifact = ArtifactFactory.create_artifact(
        artifact_type=ArtifactType.PLAN,
        name="plan",
        content={"title": "猫の雑学企画"},
        source_task_id="task_planning_001",
    )

    assert artifact.artifact_id.startswith("artifact_plan_")
    assert artifact.artifact_type == ArtifactType.PLAN
    assert artifact.name == "plan"
    assert artifact.content == {"title": "猫の雑学企画"}
    assert artifact.source_task_id == "task_planning_001"
    assert artifact.created_at is not None


def test_artifact_to_dict():
    artifact = ArtifactFactory.create_artifact(
        artifact_type=ArtifactType.SCRIPT,
        name="script",
        content={"body": "猫は人間の声を聞き分けられます。"},
        source_task_id="task_script_001",
    )

    data = artifact.to_dict()

    assert data["artifact_id"].startswith("artifact_script_")
    assert data["artifact_type"] == "script"
    assert data["name"] == "script"
    assert data["content"] == {"body": "猫は人間の声を聞き分けられます。"}
    assert data["source_task_id"] == "task_script_001"
    assert data["created_at"] == artifact.created_at


def test_artifact_source_task_id_can_be_none():
    artifact = ArtifactFactory.create_artifact(
        artifact_type=ArtifactType.GENERAL,
        name="general",
        content={"memo": "sourceなし"},
    )

    assert artifact.source_task_id is None
    assert artifact.to_dict()["source_task_id"] is None
