from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=50)


class LoginIn(BaseModel):
    account: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=64)


class SendCodeIn(BaseModel):
    email: str = Field(min_length=5, max_length=120)


class ResetPasswordIn(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=6, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    nickname: str
    avatar: str
    major: str
    role: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdateIn(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
    avatar: str | None = Field(default=None, max_length=255)
    major: str | None = Field(default=None, max_length=100)
    password: str | None = Field(default=None, min_length=6, max_length=64)


class ProgressIn(BaseModel):
    chapter_id: int | None = None
    minutes: int = Field(default=10, ge=0, le=600)


class LearningEventIn(BaseModel):
    event_type: str = Field(pattern="^(enter_chapter|heartbeat|complete_chapter)$")
    chapter_id: int | None = None
    duration_sec: int = Field(default=0, ge=0, le=3600)
    position_sec: int = Field(default=0, ge=0, le=86400)


class LearningEventsIn(BaseModel):
    events: list[LearningEventIn] = Field(min_length=1, max_length=50)


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    rating: int = Field(default=5, ge=1, le=5)


class ReplyIn(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    parent_id: int | None = None


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None
    course_id: int | None = None


class LearningPathIn(BaseModel):
    goal: str = Field(min_length=2, max_length=100)
    weekly_hours: int = Field(default=6, ge=1, le=60)
    weak_points: str = Field(default="", max_length=200)


class GradeIn(BaseModel):
    title: str = Field(default="编程作业", max_length=200)
    language: str = Field(default="python", max_length=20)
    code: str = Field(min_length=1, max_length=8000)


class ReportIn(BaseModel):
    period: str = Field(default="week", pattern="^(week|month)$")


class RoleIn(BaseModel):
    role: str = Field(pattern="^(student|teacher|admin)$")


class UserStatusIn(BaseModel):
    is_active: bool


class CourseIn(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    cover: str = Field(default="", max_length=255)
    course_type: str = Field(default="theory", pattern="^(theory|practice|certification)$")
    tech_system: str = Field(default="", max_length=30)
    tech_direction: str = Field(default="", max_length=30)
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced|co_build)$")
    is_free: bool = True
    price: float = Field(default=0, ge=0, le=99999)
    teacher_id: int | None = None
    intro: str = Field(default="", max_length=500)
    description: str = ""
    audience: str = Field(default="", max_length=200)
    prerequisite: str = ""
    status: str = Field(default="published", pattern="^(draft|published|offline)$")


class CourseUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    cover: str | None = Field(default=None, max_length=255)
    course_type: str | None = Field(default=None, pattern="^(theory|practice|certification)$")
    tech_system: str | None = Field(default=None, max_length=30)
    tech_direction: str | None = Field(default=None, max_length=30)
    level: str | None = Field(default=None, pattern="^(beginner|intermediate|advanced|co_build)$")
    is_free: bool | None = None
    price: float | None = Field(default=None, ge=0, le=99999)
    teacher_id: int | None = None
    intro: str | None = Field(default=None, max_length=500)
    description: str | None = None
    audience: str | None = Field(default=None, max_length=200)
    prerequisite: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|published|offline)$")


class ChapterIn(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    content_type: str = Field(default="video", pattern="^(video|doc|quiz)$")
    duration_min: int = Field(default=30, ge=0, le=600)
    sort: int = Field(default=0, ge=0)


class ChapterUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    content_type: str | None = Field(default=None, pattern="^(video|doc|quiz)$")
    duration_min: int | None = Field(default=None, ge=0, le=600)
    sort: int | None = Field(default=None, ge=0)


class OrderStatusIn(BaseModel):
    status: str = Field(pattern="^(pending|paid|refunded|cancelled)$")


class CourseStatusIn(BaseModel):
    status: str = Field(pattern="^(draft|published|offline)$")

class ResourceIn(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    resource_type: str = Field(default="doc", pattern="^(video|doc|code|link|lab)$")
    url: str = Field(default="", max_length=255)
    content: str = Field(default="", max_length=5000)
    sort: int = Field(default=0, ge=0)


class ResourceUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    resource_type: str | None = Field(default=None, pattern="^(video|doc|code|link|lab)$")
    url: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, max_length=5000)
    sort: int | None = Field(default=None, ge=0)


class ReviewIn(BaseModel):
    review_status: str = Field(pattern="^(published|rejected)$")
    comment: str = Field(default="", max_length=200)


class TaxonomyIn(BaseModel):
    kind: str = Field(pattern="^(course_type|tech_system|tech_direction|level)$")
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=60)
    parent_code: str | None = Field(default=None, max_length=40)
    sort: int = Field(default=0, ge=0)
    enabled: bool = True


class TaxonomyUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    parent_code: str | None = Field(default=None, max_length=40)
    sort: int | None = Field(default=None, ge=0)
    enabled: bool | None = None

class FeedbackIn(BaseModel):
    helpful: bool = True
    reason: str = Field(default="", max_length=200)


class KnowledgeIn(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    content: str = Field(min_length=10, max_length=10000)
    keywords: str = Field(default="", max_length=200)
    chapter_id: int | None = None


class KnowledgeUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    content: str | None = Field(default=None, min_length=10, max_length=10000)
    keywords: str | None = Field(default=None, max_length=200)
    chapter_id: int | None = None