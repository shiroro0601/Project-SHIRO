from typing import Protocol


class BrowserController(Protocol):
    def open(self, url: str) -> None:
        ...

    def fill(self, selector: str, value: str) -> None:
        ...

    def click(self, selector: str) -> None:
        ...

    def upload(self, selector: str, file_path: str) -> None:
        ...


class FakeBrowserController:
    def __init__(self):
        self.actions = []

    def open(self, url: str) -> None:
        self.actions.append(("open", url))

    def fill(self, selector: str, value: str) -> None:
        self.actions.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.actions.append(("click", selector))

    def upload(self, selector: str, file_path: str) -> None:
        self.actions.append(("upload", selector, file_path))

