from company.core.employee import Employee
from company.core.employee_role import EditorRole
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


class FakeGenerateEditor:
    def __init__(self, response="generated video path"):
        self.response = response
        self.tasks = []

    def generate(self, task):
        self.tasks.append(task)
        return self.response


class FakeEditEditor:
    def __init__(self, response="edited video path"):
        self.response = response
        self.tasks = []

    def edit(self, task):
        self.tasks.append(task)
        return self.response


def _task(input_data=None, instruction="猫の意外な雑学の動画を編集してください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_editor_role_name_is_editor():
    assert EditorRole().name == "Editor"


def test_editor_role_without_editor_returns_fixed_plan():
    role = EditorRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Video edit plan for: 猫の意外な雑学"


def test_editor_role_uses_topic_from_input_data():
    role = EditorRole()
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "Video edit plan for: 犬の行動心理"


def test_editor_role_with_generate_editor_calls_generate():
    editor = FakeGenerateEditor()
    role = EditorRole(editor=editor)
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "generated video path"
    assert editor.tasks == [task]


def test_editor_role_with_edit_editor_calls_edit():
    editor = FakeEditEditor()
    role = EditorRole(editor=editor)
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "edited video path"
    assert editor.tasks == [task]


def test_editor_role_finalize_returns_result():
    role = EditorRole()
    result = "Video edit plan for: 猫"

    assert role.finalize(result) == result


def test_editor_role_integrates_with_employee_execute_task():
    editor = FakeGenerateEditor(response="employee video result")
    role = EditorRole(editor=editor)
    executor = FakeTaskExecutor()
    employee = Employee(
        name="EditorEmployee",
        role=role,
        brain=FakeBrain(),
        task_executor=executor,
    )
    task = _task()

    result = employee.execute_task(task)

    assert result == "employee video result"
    assert editor.tasks == [task]
    assert executor.executed_tasks == []
