from pprint import pprint

from company.automation.browser import FakeBrowserController


def run_youtube_studio_open_check(
    browser,
    url: str = "https://studio.youtube.com",
) -> dict:
    browser.open(url)

    return {
        "status": "opened",
        "url": url,
    }


if __name__ == "__main__":
    browser = FakeBrowserController()
    result = run_youtube_studio_open_check(browser)

    print("Open check result:")
    pprint(result)
    print("\nBrowser actions:")
    pprint(browser.actions)

