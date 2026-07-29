from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT_DIR / "runtime"
PROJECTS_DIR = RUNTIME_DIR / "projects"
WINDOWS_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
    Path(r"C:\Windows\Fonts\arial.ttf"),
]


def ensure_runtime_dirs() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def get_font_path() -> Path:
    for path in WINDOWS_FONT_CANDIDATES:
        if path.exists():
            return path
    return WINDOWS_FONT_CANDIDATES[-1]

