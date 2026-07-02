from company.core.task import TaskType
from company.core.task_context import TaskContext, TaskHandoff
from company.core.task_factory import TaskFactory


def _task():
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="Task handoff test task",
        input_data={"theme": "test"},
    )


def test_task_context_can_be_created():
    task = _task()

    context = TaskContext(task=task)

    assert context.task is task
    assert context.get_artifacts() == []
    assert context.metadata == {}


def test_task_context_adds_artifact():
    context = TaskContext(task=_task())
    artifact = {
        "artifact_id": "artifact_plan_001",
        "content": {"plan": "test plan"},
    }

    context.add_artifact(artifact)

    assert context.get_artifacts() == [artifact]


def test_task_context_get_artifacts_returns_copy():
    context = TaskContext(task=_task())
    context.add_artifact({"content": "artifact"})

    artifacts = context.get_artifacts()
    artifacts.append({"content": "external mutation"})

    assert context.get_artifacts() == [{"content": "artifact"}]


def test_task_context_sets_and_gets_metadata():
    context = TaskContext(task=_task())

    context.set_metadata("priority", "high")

    assert context.get_metadata("priority") == "high"


def test_task_context_get_metadata_returns_default_when_missing():
    context = TaskContext(task=_task())

    assert context.get_metadata("missing", default="default value") == "default value"


def test_task_context_get_metadata_default_is_none_when_missing():
    context = TaskContext(task=_task())

    assert context.get_metadata("missing") is None


def test_task_handoff_can_be_created():
    context = TaskContext(task=_task())

    handoff = TaskHandoff(
        sender="Researcher",
        receiver="Writer",
        context=context,
    )

    assert handoff.sender == "Researcher"
    assert handoff.receiver == "Writer"
    assert handoff.context is context
