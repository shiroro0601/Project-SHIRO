from company.automation import playwright_environment
from company.automation.playwright_environment import PlaywrightEnvironmentCheck


def test_playwright_environment_check_returns_dict():
    result = PlaywrightEnvironmentCheck().check()

    assert isinstance(result, dict)


def test_playwright_environment_dry_run_true_is_safe():
    result = PlaywrightEnvironmentCheck(
        user_data_dir="profiles/youtube",
        dry_run=True,
    ).check()

    assert result["dry_run"] is True
    assert result["safe"] is True
    assert "dry_run is disabled. Real browser actions may run." not in result[
        "warnings"
    ]


def test_playwright_environment_dry_run_false_adds_warning():
    result = PlaywrightEnvironmentCheck(
        user_data_dir="profiles/youtube",
        dry_run=False,
    ).check()

    assert result["safe"] is False
    assert "dry_run is disabled. Real browser actions may run." in result[
        "warnings"
    ]


def test_playwright_environment_missing_user_data_dir_adds_warning():
    result = PlaywrightEnvironmentCheck(user_data_dir=None).check()

    assert "user_data_dir is not specified." in result["warnings"]


def test_playwright_environment_missing_browser_type_adds_warning():
    result = PlaywrightEnvironmentCheck(browser_type="").check()

    assert "browser_type is not specified." in result["warnings"]


def test_playwright_environment_import_failure_returns_unavailable(monkeypatch):
    def fake_find_spec(name):
        if name == "playwright":
            return None
        return object()

    monkeypatch.setattr(
        playwright_environment.importlib.util,
        "find_spec",
        fake_find_spec,
    )

    result = PlaywrightEnvironmentCheck().check()

    assert result["available"] is False


def test_playwright_environment_import_error_returns_unavailable(monkeypatch):
    def fake_find_spec(name):
        raise ImportError("playwright is not installed")

    monkeypatch.setattr(
        playwright_environment.importlib.util,
        "find_spec",
        fake_find_spec,
    )

    result = PlaywrightEnvironmentCheck().check()

    assert result["available"] is False


def test_playwright_environment_includes_settings():
    result = PlaywrightEnvironmentCheck(
        browser_type="firefox",
        headless=True,
        user_data_dir="profiles/manual",
        dry_run=True,
    ).check()

    assert result["browser_type"] == "firefox"
    assert result["headless"] is True
    assert result["user_data_dir"] == "profiles/manual"
    assert result["dry_run"] is True
