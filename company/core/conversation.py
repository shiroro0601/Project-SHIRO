from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ConversationMessage:
    employee_name: str
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class Conversation:
    conversation_id: str
    messages: List[ConversationMessage] = field(default_factory=list)

    def add_message(self, message: ConversationMessage) -> None:
        self.messages.append(message)

    def get_messages(self) -> List[ConversationMessage]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()


class ConversationRepository:
    """
    Workflow単位の短期会話履歴を保持するインメモリRepository。

    CompanyMemoryとは独立し、永続化を行わない。
    """

    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._conversations[conversation.conversation_id] = conversation

    def get(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def delete(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)

    def clear(self) -> None:
        self._conversations.clear()


class ConversationManager:
    def __init__(self, repository: ConversationRepository | None = None):
        self.repository = repository or ConversationRepository()

    def get_or_create(self, workflow_id: str) -> Conversation:
        conversation = self.repository.get(workflow_id)

        if conversation is None:
            conversation = Conversation(conversation_id=workflow_id)
            self.repository.save(conversation)

        return conversation

    def add_message(
        self,
        workflow_id: str,
        employee_name: str,
        role: str,
        content: str,
    ) -> ConversationMessage:
        conversation = self.get_or_create(workflow_id)
        message = ConversationMessage(
            employee_name=employee_name,
            role=role,
            content=content,
        )
        conversation.add_message(message)
        self.repository.save(conversation)
        return message

    def get_messages(self, workflow_id: str) -> List[ConversationMessage]:
        return self.get_or_create(workflow_id).get_messages()

    def clear(self, workflow_id: str) -> None:
        conversation = self.get_or_create(workflow_id)
        conversation.clear()
        self.repository.save(conversation)

    def dispose(self, workflow_id: str) -> None:
        self.repository.delete(workflow_id)
