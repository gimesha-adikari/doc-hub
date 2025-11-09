import os
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, UTC

REPORT_DIR = Path(__file__).resolve().parents[2] / "database" / "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

class DuplicateDetector:
    def __init__(self, root_paths):
        self.root_paths = [Path(p) for p in root_paths if Path(p).exists()]

    def _iter_files(self):
        for root in self.root_paths:
            if not root.exists():
                continue
            for p in root.rglob("*"):
                if p.is_file():
                    yield p

    @staticmethod
    def _file_hash(path):
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def find_duplicates(self):
        hash_map = defaultdict(list)
        for p in self._iter_files():
            key = self._file_hash(p)
            if not key:
                continue
            try:
                stat = p.stat()
                hash_map[key].append({
                    "path": str(p),
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
                })
            except Exception:
                continue

        duplicates = {k: v for k, v in hash_map.items() if len(v) > 1}
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "duplicate_groups": duplicates
        }

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        out_path = REPORT_DIR / f"duplicates_{timestamp}.json"

        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2)
        except Exception:
            return None, 0

        return out_path, len(duplicates)
