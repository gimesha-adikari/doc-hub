import os
import fnmatch
from pathlib import Path
from tika import parser as tika_parser

# --- IGNORE LISTS ---
IGNORED_DIRS = {
    '.git', '.hg', '.svn',
    '.idea', '.vs', '.vscode', '.config', '.local', 'snap', '.var',
    '.nuget', '.templateengine', '.java', '.dbus', '.jb_run', '.docker',
    '.designer', '.gnome', '.ssh',
    '.cache', 'JetBrains', 'Rider', 'Google', 'Android', '.dotnet', 'pnpm',
    '.nvm',
    'applications', 'icons', 'sounds', 'fonts', 'themes',
    'gnome-shell', 'gvfs-metadata', 'nautilus', 'app',
    'node_modules', '.next', '.nuxt', '.parcel-cache', '.vite',
    '.svelte-kit', '.angular', '.yarn', '.pnp', '.pnpm-store', '.vercel',
    '.netlify', '.docusaurus',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox',
    '.ipynb_checkpoints', '.venv', 'venv', 'env', '.eggs',
    '.gradle', '.build', 'build', 'out', 'libs',
    'pods', 'deriveddata',
    'bin', 'obj',
    'target',
    '.terraform', '.serverless', '.firebase', '.expo', '.dart_tool',
    'temp', 'tmp', 'logs',
    'vendor', 'plugin', 'plugins',
    '$recycle.bin', 'system volume information',
}
IGNORED_DIR_GLOBS = [
    '*.egg-info',
    'cmake-build-*',
    '*cache*'
]
IGNORED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb',
    'pipfile.lock', 'poetry.lock', 'composer.lock', 'gemfile.lock', 'cargo.lock',
    '.ds_store', 'thumbs.db', 'desktop.ini',
    'gradle-wrapper.jar', '.coverage'
}
IGNORED_FILE_GLOBS = [
    '.coverage.*',
    '*.pyc', '*.pyo', '*.pyd',
    '*.class',
    '*.o', '*.obj', '*.a', '*.so', '*.dll', '*.dylib',
    '*.min.*.map',
    '.env.*.local', '*.local.env', '.env',
    '*.log', '*.tmp', '*.temp',
    'stats.*.json', 'stats.json',
    '*.mp3', '*.wav', '*.flac', '*.m4a', '*.ogg',
    '*.mp4', '*.mkv', '*.webm', '*.avi', '*.mov', '*.wmv',
]
# --- END IGNORE LISTS ---

# --- EXTENSION LISTS ---
CODE_EXTENSIONS = {
    '.py', '.java', '.js', '.css', '.html', '.md', '.qss', '.xml',
    '.cpp', '.h', '.hpp', '.c', '.cs', '.php', '.rb', '.go', '.rs',
    '.swift', '.kt', '.scala', '.r', '.sql', '.sh', '.bat', '.ps1',
    '.yaml', '.yml', '.json', '.ts', '.jsx', '.tsx'
}
TEXT_EXTENSIONS = {
    '.txt', '.ini', '.cfg', '.conf', '.properties', '.toml'
}
COMPLEX_MIME_PREFIXES = (
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
)
# --- END EXTENSION LISTS ---


def extract_content_from_file(file_path: Path) -> (str, str):
    suffix = file_path.suffix.lower()

    if suffix in CODE_EXTENSIONS or suffix in TEXT_EXTENSIONS:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            display_type = suffix if suffix else ".txt"
            return display_type, content.strip()
        except Exception as e:
            print(f"Error reading plain text file {file_path}: {e}")
            return "unsupported", ""

    try:
        parsed_data = tika_parser.from_file(str(file_path))
        content = parsed_data.get("content") or ""
        metadata = parsed_data.get("metadata") or {}
        mime_type = metadata.get('Content-Type', 'application/octet-stream')

        if mime_type.startswith("image/"):
            return "image", ""

        if mime_type.startswith(COMPLEX_MIME_PREFIXES):
            if suffix and suffix in CODE_EXTENSIONS:
                display_type = suffix
            elif mime_type == "application/pdf":
                display_type = ".pdf"
            elif 'application/vnd.openxmlformats-officedocument' in mime_type:
                display_type = ".docx"
            elif 'application/msword' in mime_type:
                display_type = ".doc"
            else:
                display_type = suffix if suffix else "unsupported"

            return display_type, content.strip()

        if content:
            return ".txt", content.strip()

        return f"unsupported ({suffix})", ""

    except Exception as e:
        print(f"Error reading {file_path} with Tika: {e}")
        return f"unsupported ({suffix})", ""


def is_dir_ignored(dir_name: str) -> bool:
    dir_name_lower = dir_name.lower()
    if dir_name_lower in IGNORED_DIRS:
        return True
    for pattern in IGNORED_DIR_GLOBS:
        if fnmatch.fnmatch(dir_name_lower, pattern):
            return True
    return False


def is_file_ignored(file_name: str) -> bool:
    file_name_lower = file_name.lower()
    if file_name_lower in IGNORED_FILES:
        return True
    for pattern in IGNORED_FILE_GLOBS:
        if fnmatch.fnmatch(file_name_lower, pattern):
            return True
    return False