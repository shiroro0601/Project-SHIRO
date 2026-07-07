from company.brain.provider import OllamaProvider

from company.core.employee_role import (
    ResearchRole,
    WriterRole,
    ReviewerRole,
)


def main():
    provider = OllamaProvider(
        model="llama3.2:3b"
    )

    researcher = ResearchRole(provider=provider)
    writer = WriterRole(provider=provider)
    reviewer = ReviewerRole(provider=provider)

    topic = "猫の意外な雑学"

    print("=== Researcher ===")
    researcher.prepare(topic)
    research = researcher.execute(topic)
    print(research)

    print("=== Writer ===")
    writer.prepare(research)
    script = writer.execute(research)
    print(script)

    print("=== Reviewer ===")
    reviewer.prepare(script)
    review = reviewer.execute(script)
    print(review)


if __name__ == "__main__":
    main()