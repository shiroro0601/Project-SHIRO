import sys
from pprint import pprint

from company.brain.provider import OllamaProvider
from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


def run_full_ai_company_test(
    topic: str = "猫の意外な雑学",
    provider=None,
) -> dict:
    provider = provider or OllamaProvider(model="llama3.2:3b")

    researcher = ResearchRole(provider=provider)
    writer = WriterRole(provider=provider)
    reviewer = ReviewerRole(provider=provider)

    company = FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
    )

    return company.run(topic)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    topic = "猫の意外な雑学"
    print("Project SHIRO Version1.4 Full AI Company Test")
    print("Flow: Ollama AI Employees -> Dry-run Video Production Line")
    print("Provider: OllamaProvider(model='llama3.2:3b')")
    print()
    print("送信topic:")
    print(topic)
    print()

    try:
        result = run_full_ai_company_test(topic=topic)
    except RuntimeError as exc:
        print("Local Ollama request failed.")
        print("Start Ollama locally and make sure model 'llama3.2:3b' is available.")
        print(f"Reason: {exc}")
        return

    pprint(result)


if __name__ == "__main__":
    main()
