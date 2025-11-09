import csv
import fnmatch
import json
from pathlib import Path

try:
    from tika import parser as tika_parser
    _HAS_TIKA = True
except Exception:
    tika_parser = None
    _HAS_TIKA = False

from PIL import Image
import pytesseract

IGNORED_DIRS = {
    '.git', '.hg', '.svn', '.idea', '.vs', '.vscode', '.config', '.local', 'snap', '.var',
    '.nuget', '.templateengine', '.java', '.dbus', '.jb_run', '.docker', '.designer', '.gnome',
    '.ssh', '.cache', 'JetBrains', 'Rider', 'Google', 'Android', '.dotnet', '.nvm', 'applications',
    'icons', 'sounds', 'fonts', 'themes', 'gnome-shell', 'gvfs-metadata', 'nautilus', 'app',
    'node_modules', '.next', '.nuxt', '.parcel-cache', '.vite', '.svelte-kit', '.angular', '.yarn',
    '.pnp', '.pnpm-store', '.vercel', '.netlify', '.docusaurus', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.tox', '.ipynb_checkpoints', '.venv', 'venv', 'env', '.eggs',
    '.gradle', '.build', 'build', 'out', 'libs', 'pods', 'deriveddata', 'bin', 'obj', 'target',
    '.terraform', '.serverless', '.firebase', '.expo', '.dart_tool', 'temp', 'tmp', 'logs',
    'vendor', 'plugin', 'plugins', '$recycle.bin', 'system volume information',
}

IGNORED_DIR_GLOBS = ['*.egg-info', 'cmake-build-*', '*cache*']

IGNORED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb', 'pipfile.lock',
    'poetry.lock', 'composer.lock', 'gemfile.lock', 'cargo.lock', '.ds_store',
    'thumbs.db', 'desktop.ini', 'gradle-wrapper.jar', '.coverage'
}

IGNORED_FILE_GLOBS = [
    '.coverage.*', '*.pyc', '*.pyo', '*.pyd', '*.class', '*.o', '*.obj', '*.a', '*.so',
    '*.dll', '*.dylib', '*.min.*.map', '.env.*.local', '*.local.env', '.env',
    '*.log', '*.tmp', '*.temp', 'stats.*.json', 'stats.json', '*.mp3', '*.wav', '*.flac',
    '*.m4a', '*.ogg', '*.mp4', '*.mkv', '*.webm', '*.avi', '*.mov', '*.wmv'
]

CODE_EXTENSIONS = {
    '.py', '.java', '.js', '.css', '.html', '.md', '.qss', '.xml', '.cpp', '.h', '.hpp',
    '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r', '.sql',
    '.sh', '.bat', '.ps1', '.yaml', '.yml', '.json', '.ts', '.jsx', '.tsx'
}

TEXT_EXTENSIONS = {
    '.txt', '.ini', '.cfg', '.conf', '.properties', '.toml', '.csv'
}

COMPLEX_MIME_PREFIXES = (
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}


def extract_content_from_file(file_path: Path) -> (str, str, bool):
    suffix = file_path.suffix.lower()

    if suffix == ".ipynb":
        try:
            data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
            cells = ["".join(c.get("source", [])) for c in data.get("cells", [])]
            content = "\n".join(cells).strip()
            return ".ipynb", content or "[Empty Jupyter Notebook]", bool(content.strip())
        except Exception as e:
            print(f"Error reading notebook {file_path}: {e}")
            return "unsupported", "", False

    if suffix == ".csv":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = []
                for i, row in enumerate(reader):
                    rows.append(", ".join(row))
                    if i > 100:
                        break
                content = "\n".join(rows)
                return ".csv", content or "[Empty CSV]", bool(content.strip())
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
            return "unsupported", "", False

    if suffix in IMAGE_EXTENSIONS:
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang="eng").strip()
            if text:
                return "image_text", text, True
            return "image", "[No text detected in image]", False
        except Exception as e:
            print(f"OCR failed for {file_path}: {e}")
            return "image", "", False

    if suffix in CODE_EXTENSIONS or suffix in TEXT_EXTENSIONS:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            display_type = suffix if suffix else ".txt"
            return display_type, content, bool(content.strip())
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return "unsupported", "", False

    if not _HAS_TIKA:
        return f"unsupported ({suffix})", "", False

    try:
        parsed_data = tika_parser.from_file(str(file_path))
        content = parsed_data.get("content") or ""
        metadata = parsed_data.get("metadata") or {}
        mime_type = metadata.get("Content-Type", "application/octet-stream")

        if mime_type.startswith("image/"):
            return "image", "", False

        if mime_type.startswith(COMPLEX_MIME_PREFIXES):
            if suffix and suffix in CODE_EXTENSIONS:
                display_type = suffix
            elif mime_type == "application/pdf":
                display_type = ".pdf"
            elif "application/vnd.openxmlformats-officedocument" in mime_type:
                display_type = ".docx"
            elif "application/msword" in mime_type:
                display_type = ".doc"
            else:
                display_type = suffix or "unsupported"
            return display_type, content.strip(), bool(content.strip())

        if content.strip():
            return ".txt", content.strip(), True
        return f"unsupported ({suffix})", "", False
    except Exception as e:
        print(f"Error reading {file_path} with Tika: {e}")
        return f"unsupported ({suffix})", "", False


def is_dir_ignored(dir_name: str) -> bool:
    dn = dir_name.lower()
    if dn in IGNORED_DIRS:
        return True
    return any(fnmatch.fnmatch(dn, p) for p in IGNORED_DIR_GLOBS)


def is_file_ignored(file_name: str) -> bool:
    fn = file_name.lower()
    if fn in IGNORED_FILES:
        return True
    return any(fnmatch.fnmatch(fn, p) for p in IGNORED_FILE_GLOBS)
