from company.core.employee import Employee
from company.core.employee_role import VoiceRole
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
    def __init__(self, response="generated voice result"):
        self.response = response
        self.texts = []

    def generate(self, text: str) -> str:
        self.texts.append(text)
        return self.response


def _task(input_data=None, instruction="猫の意外な雑学を読み上げてください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_voice_role_name_is_voice():
    assert VoiceRole().name == "Voice"


def test_voice_role_without_generator_returns_fixed_text():
    role = VoiceRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Voice script for: 猫の意外な雑学"


def test_voice_role_uses_topic_from_input_data():
    role = VoiceRole()
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "Voice script for: 犬の行動心理"


def test_voice_role_uses_instruction_when_topic_is_missing():
    role = VoiceRole()
    task = _task(input_data={}, instruction="海の不思議を読み上げてください。")

    role.prepare(task)
    result = role.execute(task)

    assert result == "Voice script for: 海の不思議を読み上げてください。"


def test_voice_role_with_generator_calls_generate():
    generator = FakeGenerator()
    role = VoiceRole(generator=generator)
    task = _task()

    role.prepare(task)
    role.execute(task)

    assert generator.texts == ["Voice script for: 猫の意外な雑学"]


def test_voice_role_with_generator_returns_generated_result():
    generator = FakeGenerator(response="voice generated")
    role = VoiceRole(generator=generator)
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "voice generated"


def test_voice_role_finalize_returns_result():
    role = VoiceRole()
    result = "Voice script for: 猫"

    assert role.finalize(result) == result


def test_voice_role_integrates_with_employee_execute_task():
    generator = FakeGenerator(response="employee voice result")
    role = VoiceRole(generator=generator)
    executor = FakeTaskExecutor()
    employee = Employee(
        name="VoiceEmployee",
        role=role,
        brain=FakeBrain(),
        task_executor=executor,
    )
    task = _task()

    result = employee.execute_task(task)

    assert result == "employee voice result"
    assert generator.texts == ["Voice script for: 猫の意外な雑学"]
    assert executor.executed_tasks == []
