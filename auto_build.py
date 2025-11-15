import os
import subprocess
import sys
import toml
import importlib.util
import sysconfig

EXCLUDE_PACKAGES = {
    "sys", "os", "re", "json", "datetime", "pathlib", "typing",
    "shutil", "textwrap", "subprocess", "sqlite3", "__future__",
    "importlib", "fnmatch", "glob", "math", "itertools", "traceback",
    "logging", "time", "argparse", "enum", "threading", "tempfile",
    "uuid", "platform", "inspect", "collections"
}

def is_stdlib_module(module_name: str) -> bool:
    if module_name in EXCLUDE_PACKAGES:
        return True
    spec = importlib.util.find_spec(module_name)
    if not spec or not spec.origin:
        return True
    stdlib_path = sysconfig.get_paths()["stdlib"]
    return spec.origin.startswith(stdlib_path)

def detect_imports(source_dir):
    modules = set()
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("import ") or line.startswith("from "):
                            parts = line.split()
                            if parts[0] == "import":
                                modules.add(parts[1].split(".")[0])
                            elif parts[0] == "from":
                                modules.add(parts[1].split(".")[0])
    filtered = [
        m for m in modules
        if not is_stdlib_module(m)
        and not m.startswith("doc_hub")
    ]
    return filtered

def update_pyproject(dependencies):
    pyproject_path = "pyproject.toml"
    data = toml.load(pyproject_path)

    if "project" not in data:
        raise KeyError("No [project] section found in pyproject.toml")

    existing = set(data["project"].get("dependencies", []))
    new_deps = sorted(existing | set(dependencies))

    data["project"]["dependencies"] = new_deps

    with open(pyproject_path, "w") as f:
        toml.dump(data, f)

    print(f"Updated pyproject.toml with {len(dependencies)} valid dependencies:")
    for dep in new_deps:
        print(f"   - {dep}")

# --- STEP 4: Run build process ---
def main():
    print("🔍 Detecting dependencies...")
    deps = detect_imports("src")
    print("Detected imports:", ", ".join(deps))
    update_pyproject(deps)

    print("Building package...")
    subprocess.run([sys.executable, "-m", "build"], check=True)
    print("Build complete! Check the dist/ folder.")

if __name__ == "__main__":
    main()
