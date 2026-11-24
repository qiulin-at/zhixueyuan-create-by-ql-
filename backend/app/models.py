from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(50), default="")
    avatar: Mapped[str] = mapped_column(String(255), default="")
    major: Mapped[str] = mapped_column(String(100), default="")
    role: Mapped[str] = mapped_column(String(20), default="student", index=True)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), index=True)
    cover: Mapped[str] = mapped_column(String(255), default="")
    course_type: Mapped[str] = mapped_column(String(20), default="theory", index=True)
    tech_system: Mapped[str] = mapped_column(String(30), default="", index=True)
    tech_direction: Mapped[str] = mapped_column(String(30), default="", index=True)
    level: Mapped[str] = mapped_column(String(20), default="beginner", index=True)
    is_free: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    intro: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    objective: Mapped[str] = mapped_column(Text, default="[]")
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    study_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    audience: Mapped[str] = mapped_column(String(200), default="")
    prerequisite: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(16), default="published", index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    content_type: Mapped[str] = mapped_column(String(20), default="video")
    duration_min: Mapped[int] = mapped_column(Integer, default=30)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uk_user_course_fav"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearningRecord(Base):
    __tablename__ = "learning_records"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uk_user_course_learn"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    completed_chapters: Mapped[str] = mapped_column(Text, default="[]")
    last_chapter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer, default=5)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CommentReply(Base):
    __tablename__ = "comment_replies"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comment_replies.id"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CommentLike(Base):
    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="uk_user_comment_like"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="paid")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AiConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(100), default="新的对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AiMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(30), default="", index=True)
    company: Mapped[str] = mapped_column(String(120), default="")
    salary: Mapped[str] = mapped_column(String(40), default="")
    city: Mapped[str] = mapped_column(String(40), default="")
    address: Mapped[str] = mapped_column(String(200), default="")
    headcount: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text, default="")
    requirement: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uk_user_job_apply"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="applied")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "dedup_key", name="uk_user_notification_dedup"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(30), default="system", index=True)
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str] = mapped_column(String(255), default="")
    is_read: Mapped[int] = mapped_column(Integer, default=0, index=True)
    dedup_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), index=True)
    code: Mapped[str] = mapped_column(String(8))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(String(200), default="")
    kind: Mapped[str] = mapped_column(String(12), default="kb", index=True)
    resource_type: Mapped[str] = mapped_column(String(12), default="")
    url: Mapped[str] = mapped_column(String(255), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    actor_role: Mapped[str] = mapped_column(String(20), default="")
    action: Mapped[str] = mapped_column(String(50), index=True)
    target_type: Mapped[str] = mapped_column(String(30), index=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="{}")
    ip: Mapped[str] = mapped_column(String(45), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uk_user_course_enroll"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    source: Mapped[str] = mapped_column(String(16), default="free")
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TaxonomyTerm(Base):
    __tablename__ = "taxonomy_terms"
    __table_args__ = (UniqueConstraint("kind", "code", name="uk_taxonomy_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(60))
    parent_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[int] = mapped_column(Integer, default=1, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)