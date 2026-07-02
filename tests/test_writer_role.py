from company.core.employee import Employee
from company.core.employee_role import WriterRole
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


def _task(input_data=None, instruction="猫の意外な雑学の台本を書いてください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_writer_role_name_is_writer():
    assert WriterRole().name == "Writer"


def test_writer_role_prepare_can_be_called_and_stores_topic():
    role = WriterRole()
    task = _task()

    prepared_task = role.prepare(task)

    assert prepared_task is task
    assert role.topic == "猫の意外な雑学"


def test_writer_role_execute_returns_string():
    role = WriterRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert isinstance(result, str)


def test_writer_role_execute_result_contains_topic():
    role = WriterRole()
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "Script draft for: 犬の行動心理"


def test_writer_role_execute_uses_instruction_when_topic_is_missing():
    role = WriterRole()
    task = _task(input_data={}, instruction="海の不思議の台本を書いてください。")

    role.prepare(task)
    result = role.execute(task)

    assert "海の不思議の台本を書いてください。" in result


def test_writer_role_finalize_returns_result():
    role = WriterRole()
    result = "Script draft for: 猫"

    assert role.finalize(result) == result


def test_writer_role_integrates_with_employee_execute_task():
    role = WriterRole()
    executor = FakeTaskExecutor()
    employee = Employee(
        name="WriterEmployee",
        role=role,
        brain=FakeBrain(),
        task_executor=executor,
    )
    task = _task()

    result = employee.execute_task(task)

    assert result == "Script draft for: 猫の意外な雑学"
    assert executor.executed_tasks == []
