from pprint import pprint

from company.brain.provider import OllamaProvider
from company.core.employee import Employee
from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.core.task import TaskType
from company.core.task_context import TaskContext
from company.core.task_factory import TaskFactory
from company.core.task_planner import SequentialTaskPlanner
from company.core.workflow_coordinator import EmployeeRegistry, WorkflowCoordinator


def create_ai_company(provider) -> EmployeeRegistry:
    registry = EmployeeRegistry()
    registry.register(
        Employee(
            name="ResearcherEmployee",
            role=ResearchRole(provider=provider),
        )
    )
    registry.register(
        Employee(
            name="WriterEmployee",
            role=WriterRole(provider=provider),
        )
    )
    registry.register(
        Employee(
            name="ReviewerEmployee",
            role=ReviewerRole(provider=provider),
        )
    )
    return registry


def create_demo_task(theme: str = "猫の意外な雑学"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=f"{theme}についてAI会社で記事構成を作成してください。",
        input_data={"theme": theme},
    )


def run_demo(provider=None, theme: str = "猫の意外な雑学"):
    provider = provider or OllamaProvider(model="llama3")
    task = create_demo_task(theme)
    context = TaskContext(task=task)
    plan = SequentialTaskPlanner().create_plan(task)
    registry = create_ai_company(provider)
    coordinator = WorkflowCoordinator(employee_registry=registry)

    result_context = coordinator.run(plan, context)

    return {
        "task": task,
        "context": result_context,
        "artifacts": result_context.get_artifacts(),
    }


def main() -> None:
    print("Project SHIRO Version1.1 AI Company Demo")
    print("Flow: Researcher -> Writer -> Reviewer")
    print("Provider: OllamaProvider(model='llama3')")
    print()

    try:
        result = run_demo()
    except RuntimeError as exc:
        print("Local Ollama request failed.")
        print("Start Ollama locally and make sure model 'llama3' is available.")
        print(f"Reason: {exc}")
        return

    artifacts = result["artifacts"]
    print("Artifact count:", len(artifacts))
    print("Artifacts:")
    pprint(artifacts)


if __name__ == "__main__":
    main()
