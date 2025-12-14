from datetime import datetime, timezone

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, onupdate=lambda: datetime.now(timezone.utc))

class Video(Base):
    __tablename__ = "videos"

    creator_id: Mapped[str] = mapped_column(String)
    video_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reports_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    snapshots: Mapped[list["VideoSnapshot"]] = relationship(back_populates="video")


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    video_id: Mapped[str] = mapped_column(String, ForeignKey("videos.id"), nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reports_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delta_views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delta_likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delta_comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delta_reports_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    video: Mapped["Video"] = relationship(back_populates="snapshots")