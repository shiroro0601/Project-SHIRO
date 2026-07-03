import pytest

from company.core.ai_company import AICompany


class FakeRunner:
    def __init__(self):
        self.topics = []

    def run(self, topic: str):
        self.topics.append(topic)
        return {
            "status": "runner_completed",
            "topic": topic,
        }


def test_ai_company_can_be_created():
    company = AICompany()

    assert isinstance(company, AICompany)


def test_ai_company_run_returns_default_dry_run_result():
    company = AICompany()

    result = company.run("猫の意外な雑学")

    assert result == {
        "status": "completed",
        "topic": "猫の意外な雑学",
    }


def test_ai_company_run_strips_topic():
    company = AICompany()

    result = company.run("  猫の意外な雑学  ")

    assert result["topic"] == "猫の意外な雑学"


def test_ai_company_empty_topic_raises_value_error():
    company = AICompany()

    with pytest.raises(ValueError, match="topic must not be empty"):
        company.run("   ")


def test_ai_company_uses_runner_dependency():
    runner = FakeRunner()
    company = AICompany(runner=runner)

    company.run("猫の意外な雑学")

    assert runner.topics == ["猫の意外な雑学"]


def test_ai_company_returns_runner_result():
    runner = FakeRunner()
    company = AICompany(runner=runner)

    result = company.run("猫の意外な雑学")

    assert result == {
        "status": "runner_completed",
        "topic": "猫の意外な雑学",
    }


def test_ai_company_accepts_workflow_alias():
    workflow = FakeRunner()
    company = AICompany(workflow=workflow)

    result = company.run("犬の行動心理")

    assert workflow.topics == ["犬の行動心理"]
    assert result == {
        "status": "runner_completed",
        "topic": "犬の行動心理",
    }
