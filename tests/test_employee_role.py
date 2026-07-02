from company.core.employee import Employee
from company.core.employee_role import (
    DefaultEmployeeRole,
    ResearchRole,
    ReviewerRole,
    WriterRole,
)
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
        task.complete({"result": "executed"})
        return task


class RecordingRole:
    name = "Recording"

    def __init__(self):
        self.calls = []

    def prepare(self, task):
        self.calls.append(("prepare", task))
        task.input_data["prepared"] = True
        return task

    def execute(self, task):
        self.calls.append(("execute", task))
        task.input_data["role_executed"] = True
        return task

    def finalize(self, result):
        self.calls.append(("finalize", result))
        result.output_data["finalized"] = True
        return result


def _task():
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="テスト用の仕事を実行してください。",
        input_data={"theme": "test"},
    )


def test_employee_role_can_be_replaced():
    role = RecordingRole()
    employee = Employee(name="Employee", role=role, brain=FakeBrain())

    assert employee.employee_role is role
    assert employee.role == "Recording"


def test_employee_uses_default_role_when_role_is_not_specified():
    employee = Employee(name="Employee", brain=FakeBrain())

    assert isinstance(employee.employee_role, DefaultEmployeeRole)
    assert employee.role == "Default"


def test_employee_keeps_legacy_string_role_compatible():
    employee = Employee(name="Employee", role="Planner", brain=FakeBrain())

    assert isinstance(employee.employee_role, DefaultEmployeeRole)
    assert employee.role == "Planner"
    assert employee.think("hello") == "Planner: hello"


def test_research_role_name():
    assert ResearchRole().name == "Researcher"


def test_writer_role_name():
    assert WriterRole().name == "Writer"


def test_reviewer_role_name():
    assert ReviewerRole().name == "Reviewer"


def test_employee_can_receive_employee_role_separately_from_legacy_role_name():
    role = ResearchRole()
    employee = Employee(
        name="Employee",
        role="Planner",
        employee_role=role,
        brain=FakeBrain(),
    )

    assert employee.role == "Planner"
    assert employee.employee_role is role


def test_employee_execute_task_calls_prepare_execute_and_finalize():
    role = RecordingRole()
    executor = FakeTaskExecutor()
    employee = Employee(
        name="Employee",
        role=role,
        brain=FakeBrain(),
        task_executor=executor,
    )
    task = _task()

    result = employee.execute_task(task)

    assert [call[0] for call in role.calls] == ["prepare", "execute", "finalize"]
    assert executor.executed_tasks == [task]
    assert result.output_data == {
        "result": "executed",
        "finalized": True,
    }
    assert result.input_data["prepared"] is True
    assert result.input_data["role_executed"] is True


def test_default_employee_role_returns_values_unchanged():
    role = DefaultEmployeeRole()
    task = _task()
    result = {"result": "ok"}

    assert role.prepare(task) is task
    assert role.execute(task) is task
    assert role.finalize(result) is result
