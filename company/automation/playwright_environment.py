import importlib.util


class PlaywrightEnvironmentCheck:
    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = False,
        user_data_dir: str | None = None,
        dry_run: bool = True,
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.dry_run = dry_run

    def check(self) -> dict:
        warnings = []
        available = self._is_playwright_available()

        if not self.browser_type:
            warnings.append("browser_type is not specified.")

        if self.user_data_dir is None:
            warnings.append("user_data_dir is not specified.")

        if not self.dry_run:
            warnings.append("dry_run is disabled. Real browser actions may run.")

        return {
            "available": available,
            "browser_type": self.browser_type,
            "headless": self.headless,
            "user_data_dir": self.user_data_dir,
            "dry_run": self.dry_run,
            "safe": self.dry_run,
            "warnings": warnings,
        }

    def _is_playwright_available(self) -> bool:
        try:
            return importlib.util.find_spec("playwright") is not None
        except (ImportError, ValueError):
            return False

