from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Course, Favorite, LearningRecord, User
from ..schemas import UserOut, UserUpdateIn
from ..security import hash_password
from ..utils import ok

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me")
def get_me(current: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(current).model_dump())


@router.put("/me")
def update_me(
    payload: UserUpdateIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.nickname is not None:
        current.nickname = payload.nickname.strip()
    if payload.avatar is not None:
        current.avatar = payload.avatar.strip()
    if payload.major is not None:
        current.major = payload.major.strip()
    if payload.password is not None:
        current.hashed_password = hash_password(payload.password)
    db.add(current)
    db.commit()
    db.refresh(current)
    return ok(UserOut.model_validate(current).model_dump(), message="资料已更新")


@router.get("/me/favorites")
def list_favorites(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Favorite, Course)
        .join(Course, Favorite.course_id == Course.id)
        .filter(Favorite.user_id == current.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    items = [
        {
            "id": course.id,
            "title": course.title,
            "cover": course.cover,
            "tech_system": course.tech_system,
            "tech_direction": course.tech_direction,
            "level": course.level,
            "is_free": bool(course.is_free),
            "rating": round(course.rating, 1),
            "study_count": course.study_count,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None,
        }
        for fav, course in rows
    ]
    return ok({"items": items, "total": len(items)})


@router.get("/me/learning")
def list_learning(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(LearningRecord, Course)
        .join(Course, LearningRecord.course_id == Course.id)
        .filter(LearningRecord.user_id == current.id)
        .order_by(LearningRecord.updated_at.desc())
        .all()
    )
    items = [
        {
            "course_id": course.id,
            "title": course.title,
            "cover": course.cover,
            "tech_system": course.tech_system,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }
        for record, course in rows
    ]
    total_minutes = sum(item["study_minutes"] for item in items)
    return ok(
        {
            "items": items,
            "total": len(items),
            "total_minutes": total_minutes,
            "avg_progress": round(sum(item["progress"] for item in items) / len(items)) if items else 0,
        }
    )