from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..deps import get_db, require_role
from ..models import Comment, Course, Favorite, Job, JobApplication, LearningRecord, Order, User
from ..schemas import CourseStatusIn, RoleIn, UserStatusIn
from ..services.notifications import notify_course_offline
from ..utils import ok, paginated

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


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