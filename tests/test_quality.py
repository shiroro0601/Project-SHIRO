import pytest

from company.core.artifact import ArtifactFactory, ArtifactType
from company.core.quality import BasicQualityRule, QualityChecker, QualityResult


def test_quality_result_can_be_created():
    result = QualityResult(
        passed=True,
        score=0.8,
        reasons=["content is good"],
        suggestions=["keep improving"],
    )

    assert result.passed is True
    assert result.score == 0.8
    assert result.reasons == ["content is good"]
    assert result.suggestions == ["keep improving"]


def test_quality_result_score_below_zero_raises_value_error():
    with pytest.raises(ValueError):
        QualityResult(passed=False, score=-0.1)


def test_quality_result_score_above_one_raises_value_error():
    with pytest.raises(ValueError):
        QualityResult(passed=True, score=1.1)


def test_basic_quality_rule_fails_none_artifact():
    result = BasicQualityRule().check(None)

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasons == ["artifact is None"]


def test_basic_quality_rule_fails_empty_content():
    artifact = ArtifactFactory.create_artifact(
        artifact_type=ArtifactType.PLAN,
        name="plan",
        content={},
    )

    result = BasicQualityRule().check(artifact)

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasons == ["artifact content is empty"]


def test_basic_quality_rule_fails_whitespace_string_content():
    artifact = {
        "artifact_id": "artifact_general_001",
        "artifact_type": "general",
        "name": "general",
        "content": "   ",
    }

    result = BasicQualityRule().check(artifact)

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasons == ["artifact content is empty"]


def test_basic_quality_rule_passes_normal_content():
    artifact = ArtifactFactory.create_artifact(
        artifact_type=ArtifactType.SCRIPT,
        name="script",
        content={"script": "猫は人間の声を聞き分けられます。"},
    )

    result = BasicQualityRule().check(artifact)

    assert result.passed is True
    assert result.score == 1.0
    assert result.reasons == ["artifact content is present"]


def test_quality_checker_merges_multiple_rule_results():
    class PassingRule:
        def check(self, artifact):
            return QualityResult(
                passed=True,
                score=1.0,
                reasons=["passed rule"],
                suggestions=["no change"],
            )

    class PartialRule:
        def check(self, artifact):
            return QualityResult(
                passed=True,
                score=0.5,
                reasons=["partial rule"],
                suggestions=["improve detail"],
            )

    checker = QualityChecker(rules=[PassingRule(), PartialRule()])

    result = checker.check({"content": {"plan": "test"}})

    assert result.passed is True
    assert result.score == 0.75
    assert result.reasons == ["passed rule", "partial rule"]
    assert result.suggestions == ["no change", "improve detail"]


def test_quality_checker_fails_if_any_rule_fails():
    class PassingRule:
        def check(self, artifact):
            return QualityResult(passed=True, score=1.0, reasons=["passed"], suggestions=[])

    class FailingRule:
        def check(self, artifact):
            return QualityResult(passed=False, score=0.0, reasons=["failed"], suggestions=["fix it"])

    checker = QualityChecker(rules=[PassingRule(), FailingRule()])

    result = checker.check({"content": {"plan": "test"}})

    assert result.passed is False
    assert result.score == 0.5
    assert result.reasons == ["passed", "failed"]
    assert result.suggestions == ["fix it"]


def test_quality_checker_uses_basic_quality_rule_when_rules_not_specified():
    checker = QualityChecker()

    result = checker.check({"content": {"plan": "test"}})

    assert result.passed is True
    assert result.score == 1.0
