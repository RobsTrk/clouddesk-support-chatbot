from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from backend.core.config import settings

class Base(DeclarativeBase):
    pass

class Query(Base):
    __tablename__ = "queries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_query: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    response: Mapped["Response"] = relationship(back_populates="query", uselist=False)

class Response(Base):
    __tablename__ = "responses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id"), unique=True)
    answer: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    sources: Mapped[str] = mapped_column(Text)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    query: Mapped[Query] = relationship(back_populates="response")

class Escalation(Base):
    __tablename__ = "escalations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id"), unique=True)
    conversation_id: Mapped[str] = mapped_column(String(100), index=True, default="")
    intent: Mapped[str] = mapped_column(String(50), default="general_question")
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    reason: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending_human_review")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Interaction(Base):
    """Operational metadata kept separate from the original MVP tables."""
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id"), unique=True)
    conversation_id: Mapped[str] = mapped_column(String(100), index=True)
    intent: Mapped[str] = mapped_column(String(50), default="general_question")
    intent_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    retrieval_failure: Mapped[bool] = mapped_column(Boolean, default=False)
    response_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    resolved_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id"), unique=True)
    helpful: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
