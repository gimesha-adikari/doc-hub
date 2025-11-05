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


create_fts_table = DDL("""
CREATE VIRTUAL TABLE IF NOT EXISTS indexed_file_fts
USING fts5(
    file_name,
    extracted_content,
    content='indexed_file',
    content_rowid='id'
);
""")

create_insert_trigger = DDL("""
                            CREATE TRIGGER IF NOT EXISTS t_indexed_file_insert AFTER INSERT ON indexed_file
                            BEGIN
                            INSERT INTO indexed_file_fts(rowid, file_name, extracted_content)
                            VALUES (new.id, new.file_name, new.extracted_content);
                            END;
                            """)

create_update_trigger = DDL("""
                            CREATE TRIGGER IF NOT EXISTS t_indexed_file_update AFTER
                            UPDATE OF file_name, extracted_content
                            ON indexed_file
                            BEGIN
                            UPDATE indexed_file_fts
                            SET file_name         = new.file_name,
                                extracted_content = new.extracted_content
                            WHERE rowid = old.id;
                            END;
                            """)

create_delete_trigger = DDL("""
                            CREATE TRIGGER IF NOT EXISTS t_indexed_file_delete AFTER
                            DELETE
                            ON indexed_file
                            BEGIN
                            DELETE
                            FROM indexed_file_fts
                            WHERE rowid = old.id;
                            END;
                            """)

event.listen(Base.metadata, 'after_create', create_fts_table)
event.listen(Base.metadata, 'after_create', create_insert_trigger)
event.listen(Base.metadata, 'after_create', create_update_trigger)
event.listen(Base.metadata, 'after_create', create_delete_trigger)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
