from sqlalchemy import Integer, String, Enum,ForeignKey, Text,DateTime,func
from sqlalchemy.orm import Mapped, mapped_column,relationship
from .database import Base
from datetime import datetime
from typing import Optional
import enum

class Role(str,enum.Enum):
    ADMIN = "ADMIN"
    AGENT = "AGENT"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    email: Mapped[str] = mapped_column(String(255),unique=True,index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role),default=Role.AGENT)

class NoteStatus(str,enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 👈 Optional
    status: Mapped[NoteStatus] = mapped_column(Enum(NoteStatus), default=NoteStatus.queued)

    created_at: Mapped[datetime] = mapped_column(                      # 👈 Mapped[datetime]
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(                      # 👈 Mapped[datetime]
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User")

