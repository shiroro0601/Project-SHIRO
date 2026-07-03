from company.core.employee import Employee
from company.core.employee_role import ImageRole
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


class FakeGenerator:
    def __init__(self, response="generated image result"):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def _task(input_data=None, instruction="猫の意外な雑学の画像を作成してください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_image_role_name_is_image():
    assert ImageRole().name == "Image"


def test_image_role_without_generator_returns_fixed_prompt():
    role = ImageRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Image prompt for: 猫の意外な雑学"


def test_image_role_uses_topic_from_input_data():
    role = ImageRole()
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "Image prompt for: 犬の行動心理"


def test_image_role_uses_instruction_when_topic_is_missing():
    role = ImageRole()
    task = _task(input_data={}, instruction="海の不思議の画像を作成してください。")

    role.prepare(task)
    result = role.execute(task)

    assert result == "Image prompt for: 海の不思議の画像を作成してください。"


def test_image_role_with_generator_calls_generate():
    generator = FakeGenerator()
    role = ImageRole(generator=generator)
    task = _task()

    role.prepare(task)
    role.execute(task)

    assert generator.prompts == ["Image prompt for: 猫の意外な雑学"]


def test_image_role_with_generator_returns_generated_result():
    generator = FakeGenerator(response="image generated")
    role = ImageRole(generator=generator)
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "image generated"


def test_image_role_finalize_returns_result():
    role = ImageRole()
    result = "Image prompt for: 猫"

    assert role.finalize(result) == result


def test_image_role_integrates_with_employee_execute_task():
    generator = FakeGenerator(response="employee image result")
    role = ImageRole(generator=generator)
    executor = FakeTaskExecutor()
    employee = Employee(
        name="ImageEmployee",
        role=role,
        brain=FakeBrain(),
        task_executor=executor,
    )
    task = _task()

    result = employee.execute_task(task)

    assert result == "employee image result"
    assert generator.prompts == ["Image prompt for: 猫の意外な雑学"]
    assert executor.executed_tasks == []
