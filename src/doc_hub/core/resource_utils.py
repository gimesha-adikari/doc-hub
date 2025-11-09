import sys
from pathlib import Path

def get_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "resources"
    return Path(__file__).resolve().parent.parent / "resources"

def resource_path(*parts: str) -> str:
    path = get_base_path().joinpath(*parts)
    if not path.exists():
        print(f"Resource not found: {path}")
    return str(path)
