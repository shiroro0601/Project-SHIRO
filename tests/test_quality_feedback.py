from company.reports.quality_feedback import QualityFeedbackParser


def test_quality_feedback_parser_parses_passed_review():
    review_result = (
        "【評価】\n"
        "冒頭の引きがあり、分かりやすい台本です。\n\n"
        "【改善点】\n"
        "なし\n\n"
        "【判定】\n"
        "合格"
    )

    feedback = QualityFeedbackParser().parse(review_result)

    assert feedback.evaluation == "冒頭の引きがあり、分かりやすい台本です。"
    assert feedback.improvement_points == "なし"
    assert feedback.decision == "合格"
    assert feedback.score == 1.0


def test_quality_feedback_parser_parses_revision_required_review():
    review_result = (
        "【評価】\n"
        "説明が少し弱いです。\n\n"
        "【改善点】\n"
        "冒頭の引きを強くする\n\n"
        "【判定】\n"
        "修正必要"
    )

    feedback = QualityFeedbackParser().parse(review_result)

    assert feedback.evaluation == "説明が少し弱いです。"
    assert feedback.improvement_points == "冒頭の引きを強くする"
    assert feedback.decision == "修正必要"
    assert feedback.score == 0.0


def test_quality_feedback_parser_fallbacks_for_unstructured_review():
    review_result = "レビュー本文だけがあります。"

    feedback = QualityFeedbackParser().parse(review_result)

    assert feedback.evaluation == "レビュー本文だけがあります。"
    assert feedback.improvement_points == ""
    assert feedback.decision == "不明"
    assert feedback.score == 0.5


def test_quality_feedback_parser_unknown_decision_scores_half():
    review_result = (
        "【評価】\n"
        "評価本文\n\n"
        "【改善点】\n"
        "改善本文\n\n"
        "【判定】\n"
        "保留"
    )

    feedback = QualityFeedbackParser().parse(review_result)

    assert feedback.decision == "不明"
    assert feedback.score == 0.5
