import webbrowser
from pathlib import Path


class DemoService:
    def __init__(self, html_path: str):
        self.html_path = html_path

    def open_demo(self) -> bool:
        p = Path(self.html_path)
        if not p.exists():
            return False
        webbrowser.open(p.resolve().as_uri())
        return True
