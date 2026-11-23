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


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    rating: int = Field(default=5, ge=1, le=5)


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


class CourseStatusIn(BaseModel):
    status: str = Field(pattern="^(draft|published|offline)$")