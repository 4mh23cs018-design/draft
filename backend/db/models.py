import datetime
import uuid
import json
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, event
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, LargeBinary
from backend.db.database import Base

# ── Portable vector column that works on both pgvector and SQLite ──
try:
    from pgvector.sqlalchemy import Vector as PgVector
    _HAS_PGVECTOR = True
except ImportError:
    _HAS_PGVECTOR = False


class PortableVector(TypeDecorator):
    """
    Stores embedding vectors.
    - On PostgreSQL with pgvector: delegates to the native Vector type.
    - On SQLite / others: serialises to JSON text for local development.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 1536):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and _HAS_PGVECTOR:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and _HAS_PGVECTOR:
            return value  # pgvector handles list[float] natively
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)

    chunks = relationship(
        "DocumentChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True, default=1)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    # 1536 dimensions – works on Postgres (pgvector) and SQLite (JSON text)
    embedding = Column(PortableVector(1536), nullable=True)

    document = relationship("DocumentModel", back_populates="chunks")
