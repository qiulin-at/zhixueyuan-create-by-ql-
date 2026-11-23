from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..deps import get_db, require_role
from ..models import Chapter, Comment, Course, Favorite, Job, JobApplication, LearningRecord, Order, User
from ..schemas import (
    ChapterIn,
    ChapterUpdateIn,
    CourseIn,
    CourseStatusIn,
    CourseUpdateIn,
    OrderStatusIn,
    RoleIn,
    UserStatusIn,
)
from ..services.notifications import notify_course_offline
from ..utils import ok, paginated

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


def _ensure_course_access(course: Course, current: User) -> None:
    if current.role == "teacher" and course.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="只能管理本人创建的课程")


def _validate_teacher(db: Session, teacher_id: int) -> User:
    teacher = db.get(User, teacher_id)
    if teacher is None or teacher.role not in ("teacher", "admin"):
        raise HTTPException(status_code=400, detail="指定的讲师不存在")
    return teacher


def _serialize_chapter(chapter: Chapter) -> dict:
    return {
        "id": chapter.id,
        "title": chapter.title,
        "content_type": chapter.content_type,
        "duration_min": chapter.duration_min,
        "sort": chapter.sort,
    }


@router.get("/users")
def list_users(
    keyword: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if keyword.strip():
        like = f"%{keyword.strip()}%"
        query = query.filter((User.username.like(like)) | (User.nickname.like(like)) | (User.email.like(like)))
    total = query.count()
    rows = query.order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "major": user.major,
            "role": user.role,
            "is_active": bool(user.is_active),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in rows
    ]
    return ok(paginated(items, total, page, page_size))


@router.patch("/users/{user_id}/role")
def update_role(
    user_id: int,
    payload: RoleIn,
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = payload.role
    db.add(user)
    db.commit()
    return ok({"id": user.id, "role": user.role}, message="角色已更新")


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusIn,
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能停用自己的账号")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = 1 if payload.is_active else 0
    db.add(user)
    db.commit()
    return ok(
        {"id": user.id, "is_active": bool(user.is_active)},
        message="账号已启用" if payload.is_active else "账号已停用",
    )


@router.get("/courses")
def admin_list_courses(
    keyword: str = "",
    status: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    query = db.query(Course)
    if current.role == "teacher":
        query = query.filter(Course.teacher_id == current.id)
    if keyword.strip():
        query = query.filter(Course.title.like(f"%{keyword.strip()}%"))
    if status:
        query = query.filter(Course.status == status)
    total = query.count()
    rows = query.order_by(Course.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": course.id,
            "title": course.title,
            "course_type": course.course_type,
            "tech_system": course.tech_system,
            "level": course.level,
            "is_free": bool(course.is_free),
            "status": course.status,
            "study_count": course.study_count,
            "rating": round(course.rating, 1),
            "created_at": course.created_at.isoformat() if course.created_at else None,
        }
        for course in rows
    ]
    return ok(paginated(items, total, page, page_size))


@router.patch("/courses/{course_id}/status")
def update_course_status(
    course_id: int,
    payload: CourseStatusIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if current.role == "teacher" and course.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="只能管理本人创建的课程")
    previous = course.status
    course.status = payload.status
    db.add(course)
    if payload.status == "offline" and previous != "offline":
        notify_course_offline(db, course, actor_id=current.id)
    db.commit()
    return ok({"id": course.id, "status": course.status}, message="课程状态已更新")


@router.get("/courses/{course_id}")
def admin_course_detail(
    course_id: int,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    teacher = db.get(User, course.teacher_id) if course.teacher_id else None
    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course.id)
        .order_by(Chapter.sort.asc(), Chapter.id.asc())
        .all()
    )
    return ok(
        {
            "id": course.id,
            "title": course.title,
            "cover": course.cover,
            "course_type": course.course_type,
            "tech_system": course.tech_system,
            "tech_direction": course.tech_direction,
            "level": course.level,
            "is_free": bool(course.is_free),
            "price": round(float(course.price), 2),
            "teacher_id": course.teacher_id,
            "teacher_name": (teacher.nickname or teacher.username) if teacher else "",
            "intro": course.intro,
            "description": course.description,
            "status": course.status,
            "chapters": [_serialize_chapter(chapter) for chapter in chapters],
        }
    )


@router.post("/courses")
def create_course(
    payload: CourseIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    teacher_id = payload.teacher_id
    if current.role == "teacher":
        if teacher_id not in (None, current.id):
            raise HTTPException(status_code=403, detail="教师只能创建归属自己的课程")
        teacher_id = current.id
    elif teacher_id is not None:
        _validate_teacher(db, teacher_id)

    course = Course(
        title=payload.title.strip(),
        cover=payload.cover.strip(),
        course_type=payload.course_type,
        tech_system=payload.tech_system.strip(),
        tech_direction=payload.tech_direction.strip(),
        level=payload.level,
        is_free=1 if payload.is_free else 0,
        price=0.0 if payload.is_free else payload.price,
        teacher_id=teacher_id,
        intro=payload.intro.strip(),
        description=payload.description,
        status=payload.status,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return ok({"id": course.id, "title": course.title}, message="课程已创建")


@router.put("/courses/{course_id}")
def update_course(
    course_id: int,
    payload: CourseUpdateIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)

    data = payload.model_dump(exclude_unset=True)
    if "teacher_id" in data:
        if current.role != "admin":
            if data["teacher_id"] != course.teacher_id:
                raise HTTPException(status_code=403, detail="只有管理员可以变更课程归属")
        elif data["teacher_id"] is not None:
            _validate_teacher(db, data["teacher_id"])

    for field, value in data.items():
        if field == "is_free":
            value = 1 if value else 0
        setattr(course, field, value)
    if course.is_free:
        course.price = 0.0

    db.add(course)
    db.commit()
    return ok({"id": course.id, "title": course.title}, message="课程已更新")


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)

    if db.query(LearningRecord).filter(LearningRecord.course_id == course_id).first():
        raise HTTPException(status_code=409, detail="该课程已有学习记录，不能删除")
    if db.query(Order).filter(Order.course_id == course_id).first():
        raise HTTPException(status_code=409, detail="该课程已有订单，不能删除")

    db.query(Chapter).filter(Chapter.course_id == course_id).delete(synchronize_session=False)
    db.query(Comment).filter(Comment.course_id == course_id).delete(synchronize_session=False)
    db.query(Favorite).filter(Favorite.course_id == course_id).delete(synchronize_session=False)
    db.delete(course)
    db.commit()
    return ok({"id": course_id}, message="课程已删除")


@router.post("/courses/{course_id}/chapters")
def create_chapter(
    course_id: int,
    payload: ChapterIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)

    chapter = Chapter(course_id=course_id, **payload.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return ok(_serialize_chapter(chapter), message="章节已添加")


@router.put("/chapters/{chapter_id}")
def update_chapter(
    chapter_id: int,
    payload: ChapterUpdateIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    course = db.get(Course, chapter.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chapter, field, value)
    db.add(chapter)
    db.commit()
    return ok(_serialize_chapter(chapter), message="章节已更新")


@router.delete("/chapters/{chapter_id}")
def delete_chapter(
    chapter_id: int,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    course = db.get(Course, chapter.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)

    db.delete(chapter)
    db.commit()
    return ok({"id": chapter_id}, message="章节已删除")


@router.get("/teachers")
def list_teachers(
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(User)
        .filter(User.role.in_(["teacher", "admin"]), User.is_active == 1)
        .order_by(User.id.asc())
        .all()
    )
    counts = dict(
        db.query(Course.teacher_id, func.count(Course.id)).group_by(Course.teacher_id).all()
    )
    items = [
        {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "role": user.role,
            "course_count": counts.get(user.id, 0),
        }
        for user in rows
    ]
    return ok({"items": items, "total": len(items)})


@router.get("/orders")
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    total = query.count()
    rows = query.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "course_id": order.course_id,
            "amount": order.amount,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        for order in rows
    ]
    return ok(paginated(items, total, page, page_size))


ORDER_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"refunded"},
    "refunded": set(),
    "cancelled": set(),
}


@router.get("/orders/{order_id}")
def order_detail(
    order_id: int,
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    user = db.get(User, order.user_id)
    course = db.get(Course, order.course_id)
    return ok(
        {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "user_name": (user.nickname or user.username) if user else "",
            "course_id": order.course_id,
            "course_title": course.title if course else "",
            "amount": round(float(order.amount), 2),
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
    )


@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderStatusIn,
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if payload.status == order.status:
        return ok({"id": order.id, "status": order.status}, message="订单状态未变化")
    if payload.status not in ORDER_TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"订单状态不能从 {order.status} 变更为 {payload.status}",
        )
    order.status = payload.status
    db.add(order)
    db.commit()
    return ok({"id": order.id, "status": order.status}, message="订单状态已更新")


@router.get("/applications")
def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(JobApplication, Job, User).join(Job, JobApplication.job_id == Job.id).join(
        User, JobApplication.user_id == User.id
    )
    total = query.count()
    rows = query.order_by(JobApplication.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": application.id,
            "user_name": user.nickname or user.username,
            "job_title": job.title,
            "company": job.company,
            "status": application.status,
            "created_at": application.created_at.isoformat() if application.created_at else None,
        }
        for application, job, user in rows
    ]
    return ok(paginated(items, total, page, page_size))


@router.get("/stats")
def get_stats(
    current: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ok(
        {
            "users": db.query(func.count(User.id)).scalar() or 0,
            "courses": db.query(func.count(Course.id)).scalar() or 0,
            "published_courses": db.query(func.count(Course.id)).filter(Course.status == "published").scalar() or 0,
            "orders": db.query(func.count(Order.id)).scalar() or 0,
            "favorites": db.query(func.count(Favorite.id)).scalar() or 0,
            "learning_records": db.query(func.count(LearningRecord.id)).scalar() or 0,
            "comments": db.query(func.count(Comment.id)).scalar() or 0,
            "jobs": db.query(func.count(Job.id)).scalar() or 0,
            "applications": db.query(func.count(JobApplication.id)).scalar() or 0,
        }
    )