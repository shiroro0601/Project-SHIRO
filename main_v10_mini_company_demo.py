from pprint import pprint

from company.core.task import TaskType
from company.core.task_context import TaskContext
from company.core.task_factory import TaskFactory
from company.core.task_planner import SequentialTaskPlanner
from company.core.workflow_coordinator import EmployeeRegistry, WorkflowCoordinator


class DemoEmployee:
    def __init__(self, role: str, result: str, calls: list[str] | None = None):
        self.role = role
        self.result = result
        self.calls = calls if calls is not None else []

    def execute_task(self, task):
        self.calls.append(self.role)
        return {
            "employee_role": self.role,
            "task_id": task.task_id,
            "result": self.result,
        }


def create_demo_company(calls: list[str] | None = None) -> EmployeeRegistry:
    registry = EmployeeRegistry()
    registry.register(DemoEmployee("Researcher", "research result", calls))
    registry.register(DemoEmployee("Writer", "script draft", calls))
    registry.register(DemoEmployee("Reviewer", "review result", calls))
    return registry


def run_demo():
    calls: list[str] = []
    task = TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="猫の雑学動画をAI会社で企画してください。",
        input_data={"theme": "猫の雑学"},
    )
    context = TaskContext(task=task)
    plan = SequentialTaskPlanner().create_plan(task)
    registry = create_demo_company(calls)
    coordinator = WorkflowCoordinator(employee_registry=registry)

    result_context = coordinator.run(plan, context)

    return {
        "task": task,
        "context": result_context,
        "artifacts": result_context.get_artifacts(),
        "execution_order": calls,
    }


def main() -> None:
    result = run_demo()
    artifacts = result["artifacts"]

    print("Project SHIRO Mini AI Company Demo")
    print("Execution order:", " -> ".join(result["execution_order"]))
    print("Artifact count:", len(artifacts))
    print("Artifacts:")
    pprint(artifacts)


if __name__ == "__main__":
    main()
