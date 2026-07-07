from company.automation.browser import FakeBrowserController


def run_youtube_file_upload_check(
    browser,
    video_path: str,
    url: str = "https://studio.youtube.com",
) -> dict:
    if not video_path:
        raise ValueError("video_path is required")

    browser.open(url)

    browser.click("ytcp-button#create-icon")
    browser.click("tp-yt-paper-item#text-item-0")

    browser.upload(
        "input[type=file]",
        video_path,
    )

    return {
        "status": "file_selected",
        "video_path": video_path,
        "url": url,
    }


if __name__ == "__main__":
    browser = FakeBrowserController()

    result = run_youtube_file_upload_check(
        browser,
        "outputs/videos/final_video.mp4",
    )

    print(result)
    print(browser.actions)