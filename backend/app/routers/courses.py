import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_current_user_optional, get_db
from ..models import Chapter, Comment, Course, Favorite, LearningRecord, User
from ..schemas import CommentIn, ProgressIn
from ..services.notifications import notify_course_comment
from ..utils import ok, paginated

router = APIRouter(prefix="/api/courses", tags=["课程"])


def _teacher_name(teacher: User | None) -> str:
    if teacher is None:
        return "平台讲师"
    return teacher.nickname or teacher.username


def _course_item(course: Course, teacher: User | None, favorited: bool = False) -> dict:
    return {
        "id": course.id,
        "title": course.title,
        "cover": course.cover,
        "course_type": course.course_type,
        "tech_system": course.tech_system,
        "tech_direction": course.tech_direction,
        "level": course.level,
        "is_free": bool(course.is_free),
        "price": course.price,
        "teacher_name": _teacher_name(teacher),
        "rating": round(course.rating, 1),
        "rating_count": course.rating_count,
        "study_count": course.study_count,
        "intro": course.intro,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "is_favorite": favorited,
    }


@router.get("")
def list_courses(
    tech_system: str = "",
    tech_direction: str = "",
    level: str = "",
    is_free: str = "",
    course_type: str = "",
    keyword: str = "",
    sort: str = "default",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_user_optional),
):
    query = (
        db.query(Course, User)
        .outerjoin(User, Course.teacher_id == User.id)
        .filter(Course.status == "published")
    )
    if tech_system:
        query = query.filter(Course.tech_system == tech_system)
    if tech_direction:
        query = query.filter(Course.tech_direction == tech_direction)
    if level:
        query = query.filter(Course.level == level)
    if course_type:
        query = query.filter(Course.course_type == course_type)
    if is_free in {"0", "1"}:
        query = query.filter(Course.is_free == int(is_free))
    keyword = keyword.strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(Course.title.like(like), User.nickname.like(like)))

    if sort == "latest":
        query = query.order_by(Course.created_at.desc())
    elif sort == "study":
        query = query.order_by(Course.study_count.desc(), Course.rating.desc())
    elif sort == "rating":
        query = query.order_by(Course.rating.desc(), Course.rating_count.desc())
    else:
        query = query.order_by(Course.rating.desc(), Course.study_count.desc())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    favorite_ids: set[int] = set()
    if current is not None:
        favorite_ids = {
            row[0] for row in db.query(Favorite.course_id).filter(Favorite.user_id == current.id).all()
        }
    items = [_course_item(course, teacher, course.id in favorite_ids) for course, teacher in rows]
    return ok(paginated(items, total, page, page_size))


@router.get("/{course_id}")
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_user_optional),
):
    course = db.get(Course, course_id)
    if course is None or course.status == "offline":
        raise HTTPException(status_code=404, detail="课程不存在或已下架")
    teacher = db.get(User, course.teacher_id) if course.teacher_id else None
    chapters = (
        db.query(Chapter).filter(Chapter.course_id == course.id).order_by(Chapter.sort.asc(), Chapter.id.asc()).all()
    )
    favorited = False
    progress = 0
    study_minutes = 0
    if current is not None:
        favorited = (
            db.query(Favorite).filter(Favorite.user_id == current.id, Favorite.course_id == course.id).first()
            is not None
        )
        record = (
            db.query(LearningRecord)
            .filter(LearningRecord.user_id == current.id, LearningRecord.course_id == course.id)
            .first()
        )
        if record is not None:
            progress = record.progress
            study_minutes = record.study_minutes
    try:
        objectives = json.loads(course.objective) if course.objective else []
    except (TypeError, ValueError):
        objectives = []
    detail = _course_item(course, teacher, favorited)
    detail.update(
        {
            "description": course.description,
            "objectives": objectives,
            "teacher": {
                "id": teacher.id,
                "name": _teacher_name(teacher),
                "avatar": teacher.avatar if teacher else "",
                "major": teacher.major if teacher else "",
            },
            "chapters": [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "content_type": chapter.content_type,
                    "duration_min": chapter.duration_min,
                    "sort": chapter.sort,
                }
                for chapter in chapters
            ],
            "chapter_count": len(chapters),
            "progress": progress,
            "study_minutes": study_minutes,
        }
    )
    return ok(detail)


@router.post("/{course_id}/favorite")
def toggle_favorite(
    course_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    existing = (
        db.query(Favorite).filter(Favorite.user_id == current.id, Favorite.course_id == course_id).first()
    )
    if existing is not None:
        db.delete(existing)
        db.commit()
        return ok({"is_favorite": False, "course_id": course_id}, message="已取消收藏")
    db.add(Favorite(user_id=current.id, course_id=course_id))
    db.commit()
    return ok({"is_favorite": True, "course_id": course_id}, message="收藏成功")


@router.get("/{course_id}/progress")
def get_progress(
    course_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(LearningRecord)
        .filter(LearningRecord.user_id == current.id, LearningRecord.course_id == course_id)
        .first()
    )
    if record is None:
        return ok({"course_id": course_id, "progress": 0, "study_minutes": 0, "completed_chapters": []})
    try:
        completed = json.loads(record.completed_chapters) if record.completed_chapters else []
    except (TypeError, ValueError):
        completed = []
    return ok(
        {
            "course_id": course_id,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "completed_chapters": completed,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }
    )


@router.put("/{course_id}/progress")
def update_progress(
    course_id: int,
    payload: ProgressIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    total_chapters = db.query(func.count(Chapter.id)).filter(Chapter.course_id == course_id).scalar() or 0
    record = (
        db.query(LearningRecord)
        .filter(LearningRecord.user_id == current.id, LearningRecord.course_id == course_id)
        .first()
    )
    if record is None:
        record = LearningRecord(user_id=current.id, course_id=course_id, completed_chapters="[]")
        db.add(record)
        db.flush()
    try:
        completed = set(json.loads(record.completed_chapters) if record.completed_chapters else [])
    except (TypeError, ValueError):
        completed = set()
    if payload.chapter_id is not None:
        chapter = db.get(Chapter, payload.chapter_id)
        if chapter is None or chapter.course_id != course_id:
            raise HTTPException(status_code=400, detail="章节不属于该课程")
        completed.add(payload.chapter_id)
        record.last_chapter_id = payload.chapter_id
    record.completed_chapters = json.dumps(sorted(completed))
    record.progress = round(len(completed) / total_chapters * 100) if total_chapters else 0
    record.study_minutes = max(0, record.study_minutes + payload.minutes)
    db.add(record)
    db.commit()
    db.refresh(record)
    return ok(
        {
            "course_id": course_id,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "completed_chapters": sorted(completed),
        },
        message="学习进度已更新",
    )

@router.get("/{course_id}/comments")
def list_comments(
    course_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Comment, User)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.course_id == course_id)
        .order_by(Comment.id.desc())
    )
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": comment.id,
            "rating": comment.rating,
            "content": comment.content,
            "user_name": user.nickname or user.username,
            "user_avatar": user.avatar,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        }
        for comment, user in rows
    ]
    return ok(paginated(items, total, page, page_size))


@router.post("/{course_id}/comments")
def create_comment(
    course_id: int,
    payload: CommentIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    existing = (
        db.query(Comment)
        .filter(Comment.course_id == course_id, Comment.user_id == current.id)
        .first()
    )
    is_new = existing is None
    if is_new:
        comment = Comment(course_id=course_id, user_id=current.id, rating=payload.rating, content=payload.content)
        db.add(comment)
    else:
        # 同一用户同一课程只保留一条评价：再次提交视为修改，避免反复刷高评分
        comment = existing
        comment.rating = payload.rating
        comment.content = payload.content
        db.add(comment)
    db.flush()
    count = db.query(func.count(Comment.id)).filter(Comment.course_id == course_id).scalar() or 0
    average = db.query(func.avg(Comment.rating)).filter(Comment.course_id == course_id).scalar()
    course.rating = round(float(average), 1) if average is not None else course.rating
    course.rating_count = count
    db.add(course)
    if is_new:
        notify_course_comment(db, course, comment.id, actor_id=current.id)
    db.commit()
    return ok(
        {
            "course_id": course_id,
            "rating": course.rating,
            "rating_count": course.rating_count,
            "updated": not is_new,
        },
        message="评论已更新" if not is_new else "评论已发布",
    )