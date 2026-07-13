import main_v26_youtube_save_readiness_inspect as cli


class FakeBrowser:
    current_url = "https://studio.youtube.com/"

    def __init__(self):
        self.actions = []

    def is_visible(self, selector):
        self.actions.append(("is_visible", selector))
        return "Uploaded" in selector or "ytcp-uploads-dialog" in selector

    def read_text(self, selectors):
        text = " ".join(selectors)
        if "progress" in text or "Uploaded" in text:
            return "100% Uploaded"
        if "uploads-dialog" in text:
            return "Visibility"
        return ""

    def read_label(self, selectors):
        return "保存"

    def is_checked(self, selectors):
        return True

    def is_enabled(self, selectors):
        return True

    def click(self, *args):
        self.actions.append(("click", args))

    def fill_text(self, *args):
        self.actions.append(("fill_text", args))

    def upload(self, *args):
        self.actions.append(("upload", args))


def test_readiness_cli_parse_args():
    args = cli.parse_args(["--cdp-endpoint", "http://127.0.0.1:9222"])

    assert args.cdp_endpoint == "http://127.0.0.1:9222"


def test_readiness_cli_prints_read_only_state(capsys):
    browser = FakeBrowser()

    exit_code = cli.main([], browser=browser)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "current_step:" in output
    assert "upload_complete: True" in output
    assert "private_checked: True" in output
    assert "save_button_label: 保存" in output
    assert "ready_for_save: True" in output
    assert not any(action[0] in {"click", "fill_text", "upload"} for action in browser.actions)


def test_readiness_cli_import_does_not_run_main():
    assert hasattr(cli, "main")
