class PlaywrightBrowserController:
    def __init__(self, page):
        self.page = page

    def open(self, url: str) -> None:
        self.page.goto(url)

    def fill(self, selector: str, value: str) -> None:
        self.page.fill(selector, value)

    def click(self, selector: str) -> None:
        self.page.click(selector)

    def upload(self, selector: str, file_path: str) -> None:
        self.page.set_input_files(selector, file_path)

