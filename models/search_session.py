"""
Database models for documentation collection
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

Base = declarative_base()

class SearchStatus(enum.Enum):
    """Search session status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DownloadStatus(enum.Enum):
    """Download status for individual results"""
    PENDING = "pending"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"

class SearchSession(Base):
    """Search session model"""
    __tablename__ = 'search_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_query = Column(Text, nullable=False)
    search_criteria = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = Column(Enum(SearchStatus), default=SearchStatus.PENDING)
    total_results = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=True)
    
    # Relationships
    results = relationship("SearchResult", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SearchSession(id={self.id}, query='{self.original_query[:50]}...', status={self.status})>"

class SearchResult(Base):
    """Search result model"""
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('search_sessions.id'), nullable=False)
    language = Column(String(10), nullable=False)
    translated_query = Column(Text, nullable=False)
    search_engine = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
    file_size = Column(Integer, nullable=True)
    download_status = Column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    session = relationship("SearchSession", back_populates="results")
    
    def __repr__(self):
        return f"<SearchResult(id={self.id}, url='{self.url[:50]}...', status={self.download_status})>"

class TranslationCache(Base):
    """Translation cache model"""
    __tablename__ = 'translation_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<TranslationCache(id={self.id}, {self.source_language}->{self.target_language})>"
