import os

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Text, event, DDL
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


def get_session():
    return SessionLocal()
