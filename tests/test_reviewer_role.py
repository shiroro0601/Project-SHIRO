from company.core.employee import Employee
from company.core.employee_role import ReviewerRole
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


class FakeBrain:
    def ask(self, role, prompt):
        return f"{role}: {prompt}"


class FakeTaskExecutor:
    def __init__(self):
        self.executed_tasks = []

    def execute(self, task):
        self.executed_tasks.append(task)
        task.complete({"result": "executor result"})
        return task


def _task(input_data=None, instruction="猫の意外な雑学の台本をレビューしてください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_reviewer_role_name_is_reviewer():
    assert ReviewerRole().name == "Reviewer"


def test_reviewer_role_prepare_can_be_called_and_stores_topic():
    role = ReviewerRole()
    task = _task()

    prepared_task = role.prepare(task)

    assert prepared_task is task
    assert role.topic == "猫の意外な雑学"


def test_reviewer_role_execute_returns_string():
    role = ReviewerRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert isinstance(result, str)


def test_reviewer_role_execute_result_contains_review_and_approval():
    role = ReviewerRole()
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "Review result: approved for 犬の行動心理"
    assert "Review result" in result
    assert "approved" in result


def test_reviewer_role_execute_uses_instruction_when_topic_is_missing():
    role = ReviewerRole()
    task = _task(input_data={}, instruction="海の不思議の台本をレビューしてください。")

    role.prepare(task)
    result = role.execute(task)

    assert "海の不思議の台本をレビューしてください。" in result


def test_reviewer_role_finalize_returns_result():
    role = ReviewerRole()
    result = "Review result: approved for 猫"

    assert role.finalize(result) == result


def test_reviewer_role_integrates_with_employee_execute_task():
    role = ReviewerRole()
    executor = FakeTaskExecutor()
    employee = Employee(
        name="ReviewerEmployee",
        role=role,
        brain=FakeBrain(),
        task_executor=executor,
    )
    task = _task()

    result = employee.execute_task(task)

    assert result == "Review result: approved for 猫の意外な雑学"
    assert executor.executed_tasks == []
