import main_v25_youtube_cdp_lifecycle_check as cli
from company.youtube.studio_upload import CDPLifecycleCheckResult


class FakeChecker:
    def __init__(self, status="ok"):
        self.status = status
        self.called = False

    def check(self):
        self.called = True
        return CDPLifecycleCheckResult(
            status=self.status,
            first_connect=True,
            first_disconnect=True,
            chrome_alive_after_disconnect=True,
            second_connect=True,
            studio_readable=True,
            second_disconnect=True,
            chrome_alive_final=True,
            browser_close_called=False,
        )


def test_lifecycle_cli_parse_args():
    args = cli.parse_args(["--cdp-endpoint", "http://127.0.0.1:9222", "--timeout-ms", "1000"])

    assert args.cdp_endpoint == "http://127.0.0.1:9222"
    assert args.timeout_ms == 1000


def test_lifecycle_cli_success_returns_zero(capsys):
    checker = FakeChecker()

    exit_code = cli.main([], checker=checker)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert checker.called is True
    assert "status: ok" in output
    assert "browser_close_called: False" in output


def test_lifecycle_cli_failure_returns_nonzero():
    assert cli.main([], checker=FakeChecker(status="failed")) == 1


def test_lifecycle_cli_import_does_not_run_main():
    assert hasattr(cli, "main")
