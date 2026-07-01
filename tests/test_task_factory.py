from company.core.task import TaskStatus, TaskType
from company.core.task_factory import TaskFactory


def test_create_planning_task():
    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について企画を作成してください。",
        input_data={
            "theme": "猫の意外な雑学",
        },
    )

    assert task.task_id.startswith("task_planning_")
    assert task.task_type == TaskType.PLANNING
    assert task.status == TaskStatus.CREATED
    assert task.input_data["theme"] == "猫の意外な雑学"


def test_task_lifecycle_success():
    task = TaskFactory.create_task(
        task_type=TaskType.SCRIPT_WRITING,
        instruction="ショート動画用の台本を作成してください。",
    )

    task.start()

    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None

    task.complete(
        {
            "script": "猫は人間の声を聞き分けられると言われています。",
        }
    )

    assert task.status == TaskStatus.COMPLETED
    assert task.output_data["script"] == "猫は人間の声を聞き分けられると言われています。"
    assert task.finished_at is not None


def test_task_lifecycle_failed():
    task = TaskFactory.create_task(
        task_type=TaskType.QUALITY_CHECK,
        instruction="品質チェックをしてください。",
    )

    task.start()
    task.fail("テスト用エラー")

    assert task.status == TaskStatus.FAILED
    assert task.error == "テスト用エラー"
    assert task.finished_at is not None


def test_task_to_dict():
    task = TaskFactory.create_task(
        task_type=TaskType.DIRECTION,
        instruction="演出指示を作成してください。",
        input_data={
            "script": "猫の雑学台本",
        },
    )

    data = task.to_dict()

    assert data["task_type"] == "direction"
    assert data["status"] == "created"
    assert data["input_data"]["script"] == "猫の雑学台本"