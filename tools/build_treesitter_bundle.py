import subprocess
import argparse
from pathlib import Path
from tree_sitter import Language

REPOS = {
    "python": "https://github.com/tree-sitter/tree-sitter-python.git",
    "javascript": "https://github.com/tree-sitter/tree-sitter-javascript.git",
    "typescript": "https://github.com/tree-sitter/tree-sitter-typescript.git",
    "java": "https://github.com/tree-sitter/tree-sitter-java.git",
    "c": "https://github.com/tree-sitter/tree-sitter-c.git",
    "cpp": "https://github.com/tree-sitter/tree-sitter-cpp.git",
    "rust": "https://github.com/tree-sitter/tree-sitter-rust.git",
    "go": "https://github.com/tree-sitter/tree-sitter-go.git",
    "php": "https://github.com/tree-sitter/tree-sitter-php.git",
    "ruby": "https://github.com/tree-sitter/tree-sitter-ruby.git",
    "c_sharp": "https://github.com/tree-sitter/tree-sitter-c-sharp.git",
    "swift": "https://github.com/alex-pinkus/tree-sitter-swift.git"
}

def run(cmd, cwd=None):
    print("->", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)

def clone_if_missing(dest: Path, repo_url: str):
    if dest.exists():
        print(f"{dest} already exists, skipping clone.")
        return
    run(["git", "clone", "--depth", "1", repo_url, str(dest)])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="build/my-languages.so", help="Output .so/.dll/.dylib filename")
    parser.add_argument("--vendor", default="vendor", help="where to clone grammars")
    args = parser.parse_args()

    vendor_dir = Path(args.vendor).resolve()
    build_out = Path(args.out).resolve()
    build_out.parent.mkdir(parents=True, exist_ok=True)
    vendor_dir.mkdir(parents=True, exist_ok=True)

    cloned_paths = []
    for lang, repo in REPOS.items():
        dest = vendor_dir / f"tree-sitter-{lang}"
        clone_if_missing(dest, repo)

        if lang == "typescript":
            ts_dir = dest / "typescript"
            tsx_dir = dest / "tsx"
            if ts_dir.exists():
                cloned_paths.append(str(ts_dir))
            if tsx_dir.exists():
                cloned_paths.append(str(tsx_dir))
            continue

        if lang == "php":
            php_dir = dest / "php"
            if php_dir.exists():
                cloned_paths.append(str(php_dir))
                continue

        if lang == "swift":
            swift_dir = dest / "swift"
            if swift_dir.exists():
                cloned_paths.append(str(swift_dir))
                continue

        cloned_paths.append(str(dest))

    print("Building language bundle...")
    Language.build_library(
        str(build_out),
        cloned_paths
    )
    print("Built:", build_out)
    print("To use, load with: Language('" + str(build_out) + "', '<language_name>')")

if __name__ == "__main__":
    main()
