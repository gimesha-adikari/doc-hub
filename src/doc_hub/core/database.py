import os
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(DATABASE_DIR, "doc_hub.db")

engine = create_engine(f"sqlite:///{DATABASE_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class IndexedFile(Base):
    __tablename__ = "indexed_file"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    file_path = Column(String, unique=True, index=True)
    file_type = Column(String)
    file_size = Column(Integer)
    date_modified = Column(DateTime(timezone=True))
    date_indexed = Column(DateTime(timezone=True), server_default=func.now())
    extracted_content = Column(Text)
    ai_tags = Column(Text)
    ai_summary = Column(Text)

    def __repr__(self):
        return f"<IndexedFile(name='{self.file_name}', path='{self.file_path}')>"

class WatchedFolder(Base):
    __tablename__ = "watched_folder"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True)

    def __repr__(self):
        return f"<WatchedFolder(name='{self.file_path}')>"

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)
    repair_missing_schema()

def get_session():
    return SessionLocal()

def repair_missing_schema():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {row[0] for row in cur.fetchall()}

    if "indexed_file" not in existing_tables:
        cur.execute("""
        CREATE TABLE indexed_file (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT UNIQUE,
            file_type TEXT,
            file_size INTEGER,
            date_modified TEXT,
            date_indexed TEXT DEFAULT CURRENT_TIMESTAMP,
            extracted_content TEXT,
            ai_tags TEXT,
            ai_summary TEXT
        );
        """)

    if "watched_folder" not in existing_tables:
        cur.execute("""
        CREATE TABLE watched_folder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE
        );
        """)

    cur.execute("PRAGMA table_info(indexed_file);")
    existing_columns = {row[1] for row in cur.fetchall()}

    required_columns = {
        "ai_tags": "TEXT",
        "ai_summary": "TEXT",
        "extracted_content": "TEXT"
    }

    for column, col_type in required_columns.items():
        if column not in existing_columns:
            cur.execute(f"ALTER TABLE indexed_file ADD COLUMN {column} {col_type};")

    conn.commit()
    conn.close()

create_db_and_tables()
