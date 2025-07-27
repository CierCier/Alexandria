"""Database models for Alexandria memories."""

import datetime
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class Memory(Base):
    """Database model for a screenshot memory."""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    screenshot_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512), nullable=True)

    # OCR Data
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_data = Column(Text, nullable=True)  # JSON string of detailed OCR data

    # Window/Application Info
    window_title = Column(String(256), nullable=True)
    application_name = Column(String(128), nullable=True)
    window_class = Column(String(128), nullable=True)

    # Image metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)

    # Tagging and categorization
    tags = Column(Text, nullable=True)  # JSON array of tags
    is_private = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)

    # Content analysis
    has_text = Column(Boolean, default=False)
    dominant_colors = Column(Text, nullable=True)  # JSON array of hex colors

    def __repr__(self):
        return f"<Memory(id={self.id}, timestamp={self.timestamp}, path={self.screenshot_path})>"

    @property
    def tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            return []

    @tags_list.setter
    def tags_list(self, tags: List[str]):
        """Set tags from a list."""
        self.tags = json.dumps(tags)

    @property
    def ocr_data_dict(self) -> Dict[str, Any]:
        """Get OCR data as a dictionary."""
        if not self.ocr_data:
            return {}
        try:
            return json.loads(self.ocr_data)
        except json.JSONDecodeError:
            return {}

    @ocr_data_dict.setter
    def ocr_data_dict(self, data: Dict[str, Any]):
        """Set OCR data from a dictionary."""
        self.ocr_data = json.dumps(data)


class MemoryDB:
    """Database manager for Alexandria memories."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.create_tables()

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def add_memory(self, memory: Memory) -> Memory:
        """Add a new memory to the database."""
        with self.get_session() as session:
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """Get a memory by ID."""
        with self.get_session() as session:
            return session.query(Memory).filter(Memory.id == memory_id).first()

    def get_memories(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        search_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        exclude_private: bool = True,
    ) -> List[Memory]:
        """Get memories with optional filtering."""
        with self.get_session() as session:
            query = session.query(Memory)

            if exclude_private:
                query = query.filter(Memory.is_private == False)

            if start_date:
                query = query.filter(Memory.timestamp >= start_date)

            if end_date:
                query = query.filter(Memory.timestamp <= end_date)

            if search_text:
                query = query.filter(Memory.ocr_text.contains(search_text))

            if tags:
                for tag in tags:
                    query = query.filter(Memory.tags.contains(f'"{tag}"'))

            return (
                query.order_by(Memory.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    def search_memories(self, query: str, limit: int = 50) -> List[Memory]:
        """Search memories by text content."""
        with self.get_session() as session:
            return (
                session.query(Memory)
                .filter(Memory.ocr_text.contains(query))
                .filter(Memory.is_private == False)
                .order_by(Memory.timestamp.desc())
                .limit(limit)
                .all()
            )

    def get_memories_by_date(self, date: datetime.date) -> List[Memory]:
        """Get all memories from a specific date."""
        start_datetime = datetime.datetime.combine(date, datetime.time.min)
        end_datetime = datetime.datetime.combine(date, datetime.time.max)

        return self.get_memories(
            start_date=start_datetime, end_date=end_datetime, limit=1000
        )

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        with self.get_session() as session:
            memory = session.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                # Delete associated files
                if Path(memory.screenshot_path).exists():
                    Path(memory.screenshot_path).unlink()
                if memory.thumbnail_path and Path(memory.thumbnail_path).exists():
                    Path(memory.thumbnail_path).unlink()

                session.delete(memory)
                session.commit()
                return True
            return False

    def cleanup_old_memories(self, days: int) -> int:
        """Delete memories older than specified days."""
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

        with self.get_session() as session:
            old_memories = (
                session.query(Memory).filter(Memory.timestamp < cutoff_date).all()
            )

            count = 0
            for memory in old_memories:
                # Delete associated files
                if Path(memory.screenshot_path).exists():
                    Path(memory.screenshot_path).unlink()
                if memory.thumbnail_path and Path(memory.thumbnail_path).exists():
                    Path(memory.thumbnail_path).unlink()

                session.delete(memory)
                count += 1

            session.commit()
            return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            total_memories = session.query(Memory).count()
            private_memories = (
                session.query(Memory).filter(Memory.is_private == True).count()
            )
            memories_with_text = (
                session.query(Memory).filter(Memory.has_text == True).count()
            )

            # Get date range
            oldest = session.query(Memory).order_by(Memory.timestamp.asc()).first()
            newest = session.query(Memory).order_by(Memory.timestamp.desc()).first()

            return {
                "total_memories": total_memories,
                "private_memories": private_memories,
                "memories_with_text": memories_with_text,
                "oldest_memory": oldest.timestamp if oldest else None,
                "newest_memory": newest.timestamp if newest else None,
            }
