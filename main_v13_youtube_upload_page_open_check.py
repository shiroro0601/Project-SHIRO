from pprint import pprint

from company.automation.browser import FakeBrowserController


def run_youtube_upload_page_open_check(
    browser,
    url: str = "https://studio.youtube.com",
) -> dict:
    browser.open(url)
    browser.click("ytcp-button#create-icon")
    browser.click("tp-yt-paper-item#text-item-0")

    return {
        "status": "upload_page_opened",
        "url": url,
    }


if __name__ == "__main__":
    browser = FakeBrowserController()
    result = run_youtube_upload_page_open_check(browser)

    print("Upload page open check result:")
    pprint(result)
    print("\nBrowser actions:")
    pprint(browser.actions)

