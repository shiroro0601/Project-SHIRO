from dataclasses import dataclass


@dataclass
class MemoryContext:
    records: list[dict]
    prompt_text: str

    def is_empty(self) -> bool:
        return len(self.records) == 0

    def to_prompt_text(self) -> str:
        return self.prompt_text
