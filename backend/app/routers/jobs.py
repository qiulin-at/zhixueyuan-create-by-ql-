from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Job, JobApplication, User
from ..utils import ok, paginated

router = APIRouter(prefix="/api/jobs", tags=["实习就业"])


def _job_item(job: Job, detailed: bool = False) -> dict:
    item = {
        "id": job.id,
        "title": job.title,
        "category": job.category,
        "company": job.company,
        "salary": job.salary,
        "city": job.city,
        "address": job.address,
        "headcount": job.headcount,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
    if detailed:
        item.update({"description": job.description, "requirement": job.requirement})
    else:
        item["description"] = (job.description or "")[:120]
    return item


@router.get("")
def list_jobs(
    category: str = "",
    keyword: str = "",
    scope: str = "job",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Job).filter(Job.status == "published")
    if category:
        query = query.filter(Job.category == category)
    keyword = keyword.strip()
    if keyword:
        like = f"%{keyword}%"
        if scope == "company":
            query = query.filter(or_(Job.company.like(like), Job.title.like(like)))
        else:
            query = query.filter(or_(Job.title.like(like), Job.company.like(like)))
    query = query.order_by(Job.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(paginated([_job_item(job) for job in rows], total, page, page_size))


@router.get("/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_user),
):
    job = db.get(Job, job_id)
    if job is None or job.status != "published":
        raise HTTPException(status_code=404, detail="职位不存在或已下线")
    applied = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == current.id, JobApplication.job_id == job_id)
        .first()
        if current is not None
        else None
    )
    detail = _job_item(job, detailed=True)
    detail["applied"] = applied is not None
    return ok(detail)


@router.post("/{job_id}/apply")
def apply_job(
    job_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if job is None or job.status != "published":
        raise HTTPException(status_code=404, detail="职位不存在或已下线")
    existing = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == current.id, JobApplication.job_id == job_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="你已申请过该职位，请勿重复投递")
    db.add(JobApplication(user_id=current.id, job_id=job_id))
    db.commit()
    return ok({"job_id": job_id, "status": "applied"}, message="申请成功，请留意面试通知")