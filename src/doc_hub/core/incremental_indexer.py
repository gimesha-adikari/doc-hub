import hashlib
import os
import sqlite3
import time
from datetime import datetime, UTC
from pathlib import Path

from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.index import create_in, open_dir, LockError

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "index_meta.sqlite"
WHOOSH_DIR = BASE_DIR / "database" / "whoosh_index"

SCHEMA = Schema(
    path=ID(stored=True, unique=True),
    content=TEXT(analyzer=StemmingAnalyzer(), stored=False),
    updated_at=DATETIME(stored=True)
)

def safe_writer(index, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return index.writer()
        except LockError:
            print(f"Index locked (attempt {attempt + 1}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    print("Failed to acquire writer after retries.")
    return None

class IncrementalIndexer:
    def __init__(self, root_paths):
        self.root_paths = [Path(p) for p in root_paths]
        os.makedirs(DB_PATH.parent, exist_ok=True)
        os.makedirs(WHOOSH_DIR, exist_ok=True)
        self._ensure_db()
        self.ix = self._open_or_create_index()

    @staticmethod
    def _ensure_db():
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                mtime REAL,
                sha256 TEXT,
                indexed_at TEXT
            )
        """)
        con.commit()
        con.close()

    @staticmethod
    def _open_or_create_index():
        try:
            return open_dir(str(WHOOSH_DIR))
        except Exception:
            return create_in(str(WHOOSH_DIR), SCHEMA)

    @staticmethod
    def _sha256(path):
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def _gather_files(self):
        for root in self.root_paths:
            if not root.exists():
                continue
            for p in root.rglob("*"):
                if p.is_file():
                    yield p

    def reindex(self):
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        to_index = []
        for p in self._gather_files():
            try:
                stat = p.stat()
            except Exception:
                continue
            mtime = stat.st_mtime
            cur.execute("SELECT mtime, sha256 FROM files WHERE path = ?", (str(p),))
            row = cur.fetchone()
            if row is None:
                sha = self._sha256(p)
                if not sha:
                    continue
                to_index.append((p, sha))
                cur.execute(
                    "INSERT OR REPLACE INTO files(path, mtime, sha256, indexed_at) VALUES(?,?,?,?)",
                    (str(p), mtime, sha, datetime.now(UTC).isoformat())
                )
            else:
                old_mtime, old_sha = row
                if mtime != old_mtime:
                    sha = self._sha256(p)
                    if sha and sha != old_sha:
                        to_index.append((p, sha))
                    cur.execute(
                        "UPDATE files SET mtime=?, sha256=?, indexed_at=? WHERE path=?",
                        (mtime, sha or old_sha, datetime.now(UTC).isoformat(), str(p))
                    )
        con.commit()
        con.close()

        if to_index:
            writer = safe_writer(self.ix)
            if writer is None:
                return
            for p, sha in to_index:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    writer.update_document(
                        path=str(p),
                        content=text,
                        updated_at=datetime.fromtimestamp(p.stat().st_mtime, UTC)
                    )
                except Exception:
                    continue
            writer.commit()

    def drop_removed(self):
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT path FROM files")
        rows = cur.fetchall()
        removed = [p for (p,) in rows if not Path(p).exists()]
        if removed:
            cur.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in removed])
            con.commit()
            writer = safe_writer(self.ix)
            if writer is None:
                con.close()
                return
            for p in removed:
                try:
                    writer.delete_by_term("path", p)
                except Exception:
                    pass
            writer.commit()
        con.close()
