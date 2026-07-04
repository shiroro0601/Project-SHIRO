from company.automation.browser import BrowserController, FakeBrowserController


def test_fake_browser_controller_can_be_used_as_browser_controller():
    browser: BrowserController = FakeBrowserController()

    browser.open("https://studio.youtube.com")

    assert browser.actions == [("open", "https://studio.youtube.com")]


def test_fake_browser_controller_records_open():
    browser = FakeBrowserController()

    browser.open("youtube")

    assert browser.actions == [("open", "youtube")]


def test_fake_browser_controller_records_fill():
    browser = FakeBrowserController()

    browser.fill("#title", "猫の意外な雑学")

    assert browser.actions == [("fill", "#title", "猫の意外な雑学")]


def test_fake_browser_controller_records_click():
    browser = FakeBrowserController()

    browser.click("#submit")

    assert browser.actions == [("click", "#submit")]


def test_fake_browser_controller_records_upload():
    browser = FakeBrowserController()

    browser.upload("#file", "final_video.mp4")

    assert browser.actions == [("upload", "#file", "final_video.mp4")]


def test_fake_browser_controller_preserves_action_order():
    browser = FakeBrowserController()

    browser.open("https://studio.youtube.com")
    browser.fill("#title", "猫の意外な雑学")
    browser.upload("#file", "final_video.mp4")
    browser.click("#publish")

    assert browser.actions == [
        ("open", "https://studio.youtube.com"),
        ("fill", "#title", "猫の意外な雑学"),
        ("upload", "#file", "final_video.mp4"),
        ("click", "#publish"),
    ]
