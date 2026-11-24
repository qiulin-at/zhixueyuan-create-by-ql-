import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_current_user_optional, get_db
from ..models import (
    Chapter,
    Comment,
    CommentLike,
    CommentReply,
    Course,
    CourseMaterial,
    Enrollment,
    Favorite,
    LearningEvent,
    LearningRecord,
    Order,
    User,
    utcnow,
)
from ..schemas import CommentIn, LearningEventsIn, ProgressIn, ReplyIn
from ..services.notifications import notify_course_comment
from ..utils import ok, paginated

router = APIRouter(prefix="/api/courses", tags=["课程"])


def _teacher_name(teacher: User | None) -> str:
    if teacher is None:
        return "平台讲师"
    return teacher.nickname or teacher.username


def _active_enrollment(db: Session, user_id: int, course_id: int) -> Enrollment | None:
    return (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
            Enrollment.status == "active",
        )
        .first()
    )


def _ensure_enrollment(db: Session, user: User, course: Course) -> Enrollment:
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.course_id == course.id)
        .first()
    )
    if enrollment is not None and enrollment.status == "active":
        return enrollment
    if course.is_free:
        source = "free"
    else:
        paid = (
            db.query(Order)
            .filter(
                Order.user_id == user.id,
                Order.course_id == course.id,
                Order.status == "paid",
            )
            .first()
        )
        if paid is None:
            raise HTTPException(status_code=403, detail="该课程为付费课程，请先完成报名或购买")
        source = "order"
    if enrollment is None:
        enrollment = Enrollment(user_id=user.id, course_id=course.id, source=source, status="active")
        db.add(enrollment)
        course.study_count = (course.study_count or 0) + 1
        db.add(course)
    else:
        enrollment.status = "active"
        enrollment.source = source
        db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def _can_learn(db: Session, user: User | None, course: Course) -> bool:
    if user is None:
        return False
    if user.role in ("admin", "teacher"):
        return True
    return _active_enrollment(db, user.id, course.id) is not None


def _resource_item(material: CourseMaterial, chapter_title: str = "") -> dict:
    return {
        "id": material.id,
        "chapter_id": material.chapter_id,
        "chapter_title": chapter_title,
        "title": material.title,
        "resource_type": material.resource_type,
        "url": material.url,
        "content": material.content,
        "sort": material.sort,
    }


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
        .filter(Course.status == "published", Course.review_status == "published")
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
    effective_minutes = 0
    last_chapter_id = None
    last_position_sec = 0
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
            effective_minutes = record.effective_minutes
            last_chapter_id = record.last_chapter_id
            last_position_sec = record.last_position_sec
    try:
        objectives = json.loads(course.objective) if course.objective else []
    except (TypeError, ValueError):
        objectives = []
    detail = _course_item(course, teacher, favorited)
    can_learn = _can_learn(db, current, course)
    chapter_titles = {chapter.id: chapter.title for chapter in chapters}
    materials = []
    if can_learn:
        material_rows = (
            db.query(CourseMaterial)
            .filter(CourseMaterial.course_id == course.id, CourseMaterial.kind == "resource")
            .order_by(CourseMaterial.sort.asc(), CourseMaterial.id.asc())
            .all()
        )
        materials = [
            _resource_item(material, chapter_titles.get(material.chapter_id, ""))
            for material in material_rows
        ]
    detail.update(
        {
            "description": course.description,
            "objectives": objectives,
            "audience": course.audience,
            "prerequisite": course.prerequisite,
            "review_status": course.review_status,
            "last_updated_at": course.last_updated_at.isoformat() if course.last_updated_at else None,
            "is_enrolled": bool(can_learn),
            "can_learn": bool(can_learn),
            "materials": materials,
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
            "effective_minutes": effective_minutes,
            "last_chapter_id": last_chapter_id,
            "last_chapter_title": chapter_titles.get(last_chapter_id, ""),
            "last_position_sec": last_position_sec,
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


@router.post("/{course_id}/enroll")
def enroll_course(
    course_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None or course.status == "offline":
        raise HTTPException(status_code=404, detail="课程不存在或已下架")
    if current.role != "student":
        return ok(
            {"course_id": course.id, "enrolled": True, "source": "role"},
            message="教师/管理员无需报名",
        )
    enrollment = _ensure_enrollment(db, current, course)
    return ok(
        {
            "course_id": course.id,
            "enrolled": enrollment.status == "active",
            "source": enrollment.source,
        },
        message="报名成功",
    )


@router.get("/{course_id}/materials")
def list_course_materials(
    course_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None or course.status == "offline":
        raise HTTPException(status_code=404, detail="课程不存在或已下架")
    if not _can_learn(db, current, course):
        raise HTTPException(status_code=403, detail="请先报名后再查看课程资源")
    rows = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.course_id == course_id, CourseMaterial.kind == "resource")
        .order_by(CourseMaterial.sort.asc(), CourseMaterial.id.asc())
        .all()
    )
    chapter_ids = {row.chapter_id for row in rows if row.chapter_id}
    chapters = (
        {chapter.id: chapter.title for chapter in db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()}
        if chapter_ids
        else {}
    )
    items = [_resource_item(row, chapters.get(row.chapter_id, "")) for row in rows]
    return ok({"items": items, "total": len(items)})


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
        return ok(
            {
                "course_id": course_id,
                "progress": 0,
                "study_minutes": 0,
                "effective_minutes": 0,
                "completed_chapters": [],
                "last_chapter_id": None,
                "last_chapter_title": "",
                "last_position_sec": 0,
            }
        )
    try:
        completed = json.loads(record.completed_chapters) if record.completed_chapters else []
    except (TypeError, ValueError):
        completed = []
    chapter = db.get(Chapter, record.last_chapter_id) if record.last_chapter_id else None
    return ok(
        {
            "course_id": course_id,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "effective_minutes": record.effective_minutes,
            "completed_chapters": completed,
            "last_chapter_id": record.last_chapter_id,
            "last_chapter_title": chapter.title if chapter else "",
            "last_position_sec": record.last_position_sec,
            "last_accessed_at": record.last_accessed_at.isoformat() if record.last_accessed_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }
    )


@router.post("/{course_id}/events")
def report_learning_events(
    course_id: int,
    payload: LearningEventsIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None or course.status == "offline":
        raise HTTPException(status_code=404, detail="课程不存在或已下架")
    if current.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可上报学习事件")
    _ensure_enrollment(db, current, course)

    chapters = {
        chapter.id: chapter
        for chapter in db.query(Chapter).filter(Chapter.course_id == course.id).all()
    }
    record = (
        db.query(LearningRecord)
        .filter(LearningRecord.user_id == current.id, LearningRecord.course_id == course.id)
        .first()
    )
    if record is None:
        record = LearningRecord(user_id=current.id, course_id=course.id, completed_chapters="[]")
        db.add(record)
        db.flush()
    try:
        completed = set(json.loads(record.completed_chapters) if record.completed_chapters else [])
    except (TypeError, ValueError):
        completed = set()

    for event in payload.events:
        if event.chapter_id is not None and event.chapter_id not in chapters:
            raise HTTPException(status_code=400, detail="章节不属于该课程")
        duration = min(event.duration_sec, 120) if event.event_type == "heartbeat" else 0
        db.add(
            LearningEvent(
                user_id=current.id,
                course_id=course.id,
                chapter_id=event.chapter_id,
                event_type=event.event_type,
                duration_sec=duration,
                meta=json.dumps({"position_sec": event.position_sec}, ensure_ascii=False),
            )
        )
        if event.chapter_id is not None:
            record.last_chapter_id = event.chapter_id
        if event.position_sec:
            record.last_position_sec = event.position_sec
        if event.event_type == "complete_chapter" and event.chapter_id is not None:
            completed.add(event.chapter_id)
        record.last_accessed_at = utcnow()

    record.completed_chapters = json.dumps(sorted(completed))
    record.progress = round(len(completed) / len(chapters) * 100) if chapters else 0
    db.add(record)
    db.flush()

    total_seconds = (
        db.query(func.coalesce(func.sum(LearningEvent.duration_sec), 0))
        .filter(
            LearningEvent.user_id == current.id,
            LearningEvent.course_id == course.id,
            LearningEvent.event_type == "heartbeat",
        )
        .scalar()
        or 0
    )
    record.effective_minutes = round(total_seconds / 60)
    record.study_minutes = max(record.study_minutes, record.effective_minutes)
    db.add(record)
    db.commit()
    db.refresh(record)
    chapter = db.get(Chapter, record.last_chapter_id) if record.last_chapter_id else None
    return ok(
        {
            "course_id": course.id,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "effective_minutes": record.effective_minutes,
            "completed_chapters": sorted(completed),
            "last_chapter_id": record.last_chapter_id,
            "last_chapter_title": chapter.title if chapter else "",
            "last_position_sec": record.last_position_sec,
        },
        message="学习记录已更新",
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
    if current.role == "student":
        _ensure_enrollment(db, current, course)
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
    record.last_accessed_at = utcnow()
    db.add(
        LearningEvent(
            user_id=current.id,
            course_id=course_id,
            chapter_id=payload.chapter_id,
            event_type="complete_chapter",
            duration_sec=0,
            meta=json.dumps({"minutes": payload.minutes}, ensure_ascii=False),
        )
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ok(
        {
            "course_id": course_id,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "effective_minutes": record.effective_minutes,
            "completed_chapters": sorted(completed),
            "last_chapter_id": record.last_chapter_id,
            "last_position_sec": record.last_position_sec,
        },
        message="学习进度已更新",
    )

def _get_comment_or_404(db: Session, course_id: int, comment_id: int) -> Comment:
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.course_id == course_id)
        .first()
    )
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    return comment


@router.get("/{course_id}/comments")
def list_comments(
    course_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current: User | None = Depends(get_current_user_optional),
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
    comment_ids = [comment.id for comment, _ in rows]
    like_counts: dict[int, int] = {}
    reply_counts: dict[int, int] = {}
    liked_ids: set[int] = set()
    if comment_ids:
        like_counts = dict(
            db.query(CommentLike.comment_id, func.count(CommentLike.id))
            .filter(CommentLike.comment_id.in_(comment_ids))
            .group_by(CommentLike.comment_id)
            .all()
        )
        reply_counts = dict(
            db.query(CommentReply.comment_id, func.count(CommentReply.id))
            .filter(CommentReply.comment_id.in_(comment_ids))
            .group_by(CommentReply.comment_id)
            .all()
        )
        if current is not None:
            liked_ids = {
                row[0]
                for row in db.query(CommentLike.comment_id)
                .filter(CommentLike.user_id == current.id, CommentLike.comment_id.in_(comment_ids))
                .all()
            }
    items = [
        {
            "id": comment.id,
            "rating": comment.rating,
            "content": comment.content,
            "user_name": user.nickname or user.username,
            "user_avatar": user.avatar,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "likes_count": like_counts.get(comment.id, 0),
            "replies_count": reply_counts.get(comment.id, 0),
            "liked_by_me": comment.id in liked_ids,
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

@router.get("/{course_id}/comments/{comment_id}/replies")
def list_replies(
    course_id: int,
    comment_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    _get_comment_or_404(db, course_id, comment_id)
    query = (
        db.query(CommentReply, User)
        .join(User, CommentReply.user_id == User.id)
        .filter(CommentReply.comment_id == comment_id)
        .order_by(CommentReply.id.asc())
    )
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": reply.id,
            "comment_id": reply.comment_id,
            "parent_id": reply.parent_id,
            "content": reply.content,
            "user_name": user.nickname or user.username,
            "user_avatar": user.avatar,
            "created_at": reply.created_at.isoformat() if reply.created_at else None,
        }
        for reply, user in rows
    ]
    return ok(paginated(items, total, page, page_size))


@router.post("/{course_id}/comments/{comment_id}/replies")
def create_reply(
    course_id: int,
    comment_id: int,
    payload: ReplyIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_comment_or_404(db, course_id, comment_id)
    if payload.parent_id is not None:
        parent = (
            db.query(CommentReply)
            .filter(CommentReply.id == payload.parent_id, CommentReply.comment_id == comment_id)
            .first()
        )
        if parent is None:
            raise HTTPException(status_code=404, detail="父回复不存在")
    reply = CommentReply(
        comment_id=comment_id,
        user_id=current.id,
        parent_id=payload.parent_id,
        content=payload.content,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return ok(
        {
            "id": reply.id,
            "comment_id": reply.comment_id,
            "parent_id": reply.parent_id,
            "content": reply.content,
            "user_name": current.nickname or current.username,
            "created_at": reply.created_at.isoformat() if reply.created_at else None,
        },
        message="回复已发布",
    )


@router.post("/{course_id}/comments/{comment_id}/like")
def toggle_comment_like(
    course_id: int,
    comment_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_comment_or_404(db, course_id, comment_id)
    existing = (
        db.query(CommentLike)
        .filter(CommentLike.user_id == current.id, CommentLike.comment_id == comment_id)
        .first()
    )
    if existing is None:
        db.add(CommentLike(user_id=current.id, comment_id=comment_id))
        liked = True
    else:
        db.delete(existing)
        liked = False
    db.commit()
    likes_count = db.query(func.count(CommentLike.id)).filter(CommentLike.comment_id == comment_id).scalar() or 0
    return ok({"liked": liked, "likes_count": likes_count}, message="已点赞" if liked else "已取消点赞")