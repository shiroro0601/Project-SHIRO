from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


class FakeProvider:
    def __init__(self, response="generated text"):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def _task(input_data=None, instruction="猫の意外な雑学について作業してください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_research_role_without_provider_keeps_existing_behavior():
    role = ResearchRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Research result for: 猫の意外な雑学"


def test_writer_role_without_provider_keeps_existing_behavior():
    role = WriterRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Script draft for: 猫の意外な雑学"


def test_reviewer_role_without_provider_keeps_existing_behavior():
    role = ReviewerRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Review result: approved for 猫の意外な雑学"


def test_research_role_uses_provider_with_research_prompt():
    provider = FakeProvider(response="provider research result")
    role = ResearchRole(provider=provider)
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider research result"
    assert provider.prompts == [
        "次のテーマについて調査してください: 猫の意外な雑学"
    ]


def test_writer_role_uses_provider_with_writer_prompt():
    provider = FakeProvider(response="provider script draft")
    role = WriterRole(provider=provider)
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider script draft"
    assert provider.prompts == [
        "次のテーマについてYouTubeショート用の台本を書いてください: 犬の行動心理"
    ]


def test_reviewer_role_uses_provider_with_reviewer_prompt():
    provider = FakeProvider(response="provider review result")
    role = ReviewerRole(provider=provider)
    task = _task(input_data={"title": "海の不思議"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider review result"
    assert provider.prompts == [
        "次の成果物をレビューしてください: 海の不思議"
    ]


def test_provider_generate_result_becomes_execute_return_value():
    provider = FakeProvider(response="exact generated value")
    role = ResearchRole(provider=provider)
    task = _task()

    role.prepare(task)

    assert role.execute(task) == "exact generated value"
