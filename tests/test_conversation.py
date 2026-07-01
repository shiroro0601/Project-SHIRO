from company.core.conversation import (
    Conversation,
    ConversationManager,
    ConversationMessage,
    ConversationRepository,
)


def test_conversation_adds_and_gets_messages():
    conversation = Conversation(conversation_id="workflow_001")
    message = ConversationMessage(
        employee_name="PlannerAI",
        role="Planner",
        content="企画を作成します。",
    )

    conversation.add_message(message)

    messages = conversation.get_messages()
    assert len(messages) == 1
    assert messages[0].employee_name == "PlannerAI"
    assert messages[0].role == "Planner"
    assert messages[0].content == "企画を作成します。"
    assert messages[0].timestamp is not None


def test_conversation_clear_removes_messages():
    conversation = Conversation(conversation_id="workflow_001")
    conversation.add_message(
        ConversationMessage(
            employee_name="ScriptWriterAI",
            role="ScriptWriter",
            content="台本を作成します。",
        )
    )

    conversation.clear()

    assert conversation.get_messages() == []


def test_repository_keeps_workflow_conversations_independent():
    repository = ConversationRepository()
    first = Conversation(conversation_id="workflow_001")
    second = Conversation(conversation_id="workflow_002")

    first.add_message(
        ConversationMessage(
            employee_name="PlannerAI",
            role="Planner",
            content="workflow_001 message",
        )
    )
    second.add_message(
        ConversationMessage(
            employee_name="DirectorAI",
            role="Director",
            content="workflow_002 message",
        )
    )
    repository.save(first)
    repository.save(second)

    assert repository.get("workflow_001").get_messages()[0].content == "workflow_001 message"
    assert repository.get("workflow_002").get_messages()[0].content == "workflow_002 message"


def test_manager_creates_conversation_and_adds_message():
    manager = ConversationManager()

    message = manager.add_message(
        workflow_id="workflow_001",
        employee_name="PlannerAI",
        role="Planner",
        content="企画を開始します。",
    )

    messages = manager.get_messages("workflow_001")
    assert message in messages
    assert messages[0].content == "企画を開始します。"


def test_manager_clear_keeps_conversation_but_removes_messages():
    manager = ConversationManager()
    manager.add_message(
        workflow_id="workflow_001",
        employee_name="ArtistAI",
        role="Artist",
        content="画像プロンプトを作ります。",
    )

    manager.clear("workflow_001")

    assert manager.get_messages("workflow_001") == []


def test_manager_dispose_removes_workflow_conversation():
    repository = ConversationRepository()
    manager = ConversationManager(repository=repository)
    manager.add_message(
        workflow_id="workflow_001",
        employee_name="DirectorAI",
        role="Director",
        content="演出を確認します。",
    )

    manager.dispose("workflow_001")

    assert repository.get("workflow_001") is None


def test_manager_uses_injected_repository():
    repository = ConversationRepository()
    manager = ConversationManager(repository=repository)

    manager.add_message(
        workflow_id="workflow_001",
        employee_name="PlannerAI",
        role="Planner",
        content="DIされたRepositoryに保存します。",
    )

    assert repository.get("workflow_001") is not None
    assert repository.get("workflow_001").get_messages()[0].content == "DIされたRepositoryに保存します。"
