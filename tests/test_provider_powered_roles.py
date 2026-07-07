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
    prompt = provider.prompts[0]
    assert "YouTubeショート動画のリサーチャー" in prompt
    assert "日本語" in prompt
    assert "5個" in prompt
    assert "雑学" in prompt
    assert "テーマ" in prompt
    assert "テーマから逸脱してはいけません" in prompt
    assert "別テーマを提案してはいけません" in prompt
    assert "今回の調査テーマ:" in prompt
    assert "あなたは指定テーマ専門のリサーチ担当です。" in prompt
    assert "指定テーマ以外を書いてはいけません。" in prompt
    assert "知らない場合でも別テーマへ変更禁止。" in prompt
    assert "出力形式" in prompt
    assert "猫の意外な雑学" in prompt


def test_writer_role_uses_provider_with_writer_prompt():
    provider = FakeProvider(response="provider script draft")
    role = WriterRole(provider=provider)
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider script draft"
    prompt = provider.prompts[0]
    assert "YouTubeショート動画の台本作家" in prompt
    assert "60秒以内" in prompt
    assert "リサーチ結果だけを材料" in prompt
    assert "入力された調査結果だけを使う" in prompt
    assert "入力された調査結果:" in prompt
    assert "調査結果以外は禁止" in prompt
    assert "動物変更禁止" in prompt
    assert "新しいテーマを作らない" in prompt
    assert "推測追加禁止" in prompt
    assert "無関係な話題に移らない" in prompt
    assert "出力形式" in prompt
    assert "【タイトル】" in prompt
    assert "【ナレーション】" in prompt
    assert "【画像指示】" in prompt
    assert "犬の行動心理" in prompt


def test_reviewer_role_uses_provider_with_reviewer_prompt():
    provider = FakeProvider(response="provider review result")
    role = ReviewerRole(provider=provider)
    task = _task(input_data={"title": "海の不思議"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider review result"
    prompt = provider.prompts[0]
    assert "YouTubeショート動画の編集長" in prompt
    assert "合格" in prompt
    assert "修正必要" in prompt
    assert "改善点" in prompt
    assert "以下の台本だけをレビュー" in prompt
    assert "評価対象台本:" in prompt
    assert "「内容がない」「不明」とは言わないでください" in prompt
    assert "合格」または「修正必要」のどちらかだけ" in prompt
    assert "「合格ですが修正必要」は禁止です。" in prompt
    assert "「一応合格」は禁止です。" in prompt
    assert "「改善推奨だが合格」は禁止です。" in prompt
    assert "テーマ不一致なら必ず「修正必要」と判定してください。" in prompt
    assert "改善点が1つでもある場合は「修正必要」と判定してください。" in prompt
    assert "必ず【評価】【改善点】【判定】の3ブロック" in prompt
    assert "【改善点】には具体的な修正案" in prompt
    assert "【判定】の次の1行には「合格」または「修正必要」だけ" in prompt
    assert "出力形式" in prompt
    assert "海の不思議" in prompt


def test_provider_generate_result_becomes_execute_return_value():
    provider = FakeProvider(response="exact generated value")
    role = ResearchRole(provider=provider)
    task = _task()

    role.prepare(task)

    assert role.execute(task) == "exact generated value"


def test_research_role_direct_topic_is_in_prompt_and_not_unknown():
    provider = FakeProvider(response="research")
    role = ResearchRole(provider=provider)

    result = role.execute("猫の意外な雑学")

    assert result == "research"
    prompt = provider.prompts[0]
    assert "猫の意外な雑学" in prompt
    assert "unknown topic" not in prompt
    assert "猫に直接関係する雑学だけ" in prompt
    assert "【調査テーマ】" in prompt
    assert "【雑学1】" in prompt
    assert "【理由5】" in prompt


def test_research_direct_string_input():
    provider = FakeProvider(response="research")
    role = ResearchRole(provider=provider)

    result = role.execute("猫の意外な雑学")

    assert result == "research"
    prompt = provider.prompts[0]
    assert "今回の調査テーマ:\n猫の意外な雑学" in prompt
    assert "猫の意外な雑学" in prompt
    assert "unknown topic" not in prompt


def test_research_role_empty_topic_uses_unknown_topic():
    provider = FakeProvider(response="research")
    role = ResearchRole(provider=provider)

    role.execute("")

    assert "unknown topic" in provider.prompts[0]


def test_writer_role_direct_research_result_is_in_prompt():
    provider = FakeProvider(response="script")
    role = WriterRole(provider=provider)
    research_result = "【調査テーマ】猫の意外な雑学\n【雑学1】猫はひげで幅を測る"

    result = role.execute(research_result)

    assert result == "script"
    prompt = provider.prompts[0]
    assert research_result in prompt
    assert "入力された調査結果だけを使う" in prompt
    assert "入力された調査結果:" in prompt
    assert "調査結果以外は禁止" in prompt
    assert "動物変更禁止" in prompt
    assert "推測追加禁止" in prompt
    assert "ゲーム、車、パソコンなどへ変更しない" in prompt
    assert "【タイトル】" in prompt
    assert "【ナレーション】" in prompt
    assert "【画像指示】" in prompt


def test_writer_direct_string_input():
    provider = FakeProvider(response="script")
    role = WriterRole(provider=provider)
    research_result = "猫は液体のように狭い場所に入れる"

    result = role.execute(research_result)

    assert result == "script"
    prompt = provider.prompts[0]
    assert f"入力された調査結果:\n{research_result}" in prompt
    assert research_result in prompt
    assert "入力された調査結果だけを使う" in prompt


def test_writer_role_prefers_research_result_over_theme():
    provider = FakeProvider(response="script")
    role = WriterRole(provider=provider)
    task = _task(
        input_data={
            "theme": "猫の意外な雑学",
            "research_result": "猫だけに関係する調査結果",
        }
    )

    role.prepare(task)
    role.execute(task)

    prompt = provider.prompts[0]
    assert "猫だけに関係する調査結果" in prompt


def test_reviewer_role_direct_script_is_in_prompt():
    provider = FakeProvider(response="review")
    role = ReviewerRole(provider=provider)
    script = "【タイトル】猫の意外な雑学\n【ナレーション】猫のひげはセンサーです。"

    result = role.execute(script)

    assert result == "review"
    prompt = provider.prompts[0]
    assert script in prompt
    assert "以下の台本だけをレビュー" in prompt
    assert "評価対象台本:" in prompt
    assert "「内容がない」「不明」とは言わないでください" in prompt
    assert "合格」または「修正必要」のどちらかだけ" in prompt
    assert "矛盾した判定は禁止" in prompt
    assert "「合格ですが修正必要」は禁止です。" in prompt
    assert "「一応合格」は禁止です。" in prompt
    assert "「改善推奨だが合格」は禁止です。" in prompt
    assert "必ず【評価】【改善点】【判定】の3ブロック" in prompt
    assert "【判定】の次の1行には「合格」または「修正必要」だけ" in prompt


def test_reviewer_direct_string_input():
    provider = FakeProvider(response="review")
    role = ReviewerRole(provider=provider)
    script = "猫動画台本"

    result = role.execute(script)

    assert result == "review"
    prompt = provider.prompts[0]
    assert f"評価対象台本:\n{script}" in prompt
    assert script in prompt
    assert "合格」または「修正必要」のどちらかだけ" in prompt
    assert "【判定】の次の1行には「合格」または「修正必要」だけ" in prompt


def test_reviewer_role_prefers_script_result_over_theme():
    provider = FakeProvider(response="review")
    role = ReviewerRole(provider=provider)
    task = _task(
        input_data={
            "theme": "猫の意外な雑学",
            "script_result": "猫だけに関係する台本",
        }
    )

    role.prepare(task)
    role.execute(task)

    prompt = provider.prompts[0]
    assert "猫だけに関係する台本" in prompt
