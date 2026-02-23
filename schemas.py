from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    nodes: Mapped[list["Node"]] = relationship("Node", back_populates="scene", cascade="all, delete-orphan")

class Node(Base):
    __tablename__ = "nodes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), index=True)

    key: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., grammar, ad_law
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)        # flow order
    x: Mapped[int] = mapped_column(Integer, default=60)           # UI position
    y: Mapped[int] = mapped_column(Integer, default=160)

    prompt_template: Mapped[str] = mapped_column(Text, default="") # contains {text}

    scene: Mapped["Scene"] = relationship("Scene", back_populates="nodes")

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(Integer, index=True)

    status: Mapped[str] = mapped_column(String(32), default="done") # queued/running/done/failed
    conclusion: Mapped[str] = mapped_column(String(32), default="—")
    risk: Mapped[str] = mapped_column(String(16), default="—")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    input_text: Mapped[str] = mapped_column(Text, default="")
    results: Mapped[dict] = mapped_column(JSON, default=dict)  # {node_key: llm_json_or_text}
    merged: Mapped[dict] = mapped_column(JSON, default=dict)   # merged final json
