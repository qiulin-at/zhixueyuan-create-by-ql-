import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db, require_role
from ..models import Assignment, Chapter, Course, Enrollment, Submission, User, utcnow
from ..schemas import AssignmentIn, AssignmentUpdateIn, SubmissionIn, SubmissionReviewIn
from ..services import audit, sandbox
from ..services.llm import llm_gateway
from ..services.mock_engine import mock_grade
from ..services.prompts import GRADE_SYSTEM
from ..services.user_llm import resolve_user_config
from ..utils import ok

router = APIRouter(prefix="/api", tags=["作业与批改"])

DEFAULT_RUBRIC = {
    "dimensions": [
        {"key": "correctness", "name": "功能正确性", "weight": 0.5},
        {"key": "boundary", "name": "边界处理", "weight": 0.2},
        {"key": "efficiency", "name": "算法效率", "weight": 0.15},
        {"key": "quality", "name": "代码规范", "weight": 0.15},
    ],
    "pass_line": 60,
}


def _loads(raw: str, fallback):
    try:
        value = json.loads(raw or "")
        return value if isinstance(value, type(fallback)) else fallback
    except (TypeError, ValueError):
        return fallback


def _parse_json(content: str | None) -> dict:
    if not content:
        return {}
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        value = json.loads(text[start : end + 1])
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def _parse_deadline(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="截止时间格式应为 ISO 格式，例如 2026-12-01T18:00:00",
        ) from exc


def _ensure_course_access(course: Course, current: User) -> None:
    if current.role == "admin":
        return
    if current.role == "teacher" and course.teacher_id == current.id:
        return
    raise HTTPException(status_code=403, detail="无权访问该课程")


def _ensure_enrolled(db: Session, current: User, course: Course) -> None:
    if current.role in ("admin", "teacher"):
        return
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current.id,
            Enrollment.course_id == course.id,
            Enrollment.status == "active",
        )
        .first()
    )
    if enrollment is None:
        raise HTTPException(status_code=403, detail="请先报名课程后再查看或提交作业")


def _assignment_dict(assignment: Assignment, submitted=None, include_hidden=False) -> dict:
    data = {
        "id": assignment.id,
        "course_id": assignment.course_id,
        "chapter_id": assignment.chapter_id,
        "title": assignment.title,
        "description": assignment.description,
        "language": assignment.language,
        "deadline": assignment.deadline.isoformat() if assignment.deadline else None,
        "rubric": _loads(assignment.rubric_json, {}),
        "sample_cases": _loads(assignment.sample_cases_json, []),
        "status": assignment.status,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
    }
    if include_hidden:
        data["hidden_cases"] = _loads(assignment.hidden_cases_json, [])
    if submitted is not None:
        data["my_submission"] = submitted
    return data


def _load_test_result(raw: str):
    try:
        value = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    if isinstance(value, dict):
        return value
    return {"cases": value} if isinstance(value, list) else {}


def _submission_dict(submission: Submission, include_code=True) -> dict:
    data = {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "user_id": submission.user_id,
        "attempt": submission.attempt,
        "status": submission.status,
        "test_result": _load_test_result(submission.test_result_json),
        "objective_score": submission.objective_score,
        "ai_feedback": _loads(submission.ai_feedback_json, {}),
        "ai_score": submission.ai_score,
        "final_score": submission.final_score,
        "review_comment": submission.review_comment,
        "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
    }
    if include_code:
        data["code"] = submission.code
    return data


def _ai_review(
    assignment: Assignment,
    code: str,
    user_config: dict | None = None,
) -> tuple[dict, str, str]:
    prompt = GRADE_SYSTEM.format(title=assignment.title, language=assignment.language)
    content, llm_source = llm_gateway.chat_ex(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": code},
        ],
        temperature=0.2,
        max_tokens=1200,
        json_mode=True,
        user_config=user_config,
    )
    mode = "online" if llm_source in ("user", "platform") else "mock"
    parsed = _parse_json(content)
    if not parsed:
        parsed = _parse_json(mock_grade(assignment.title, assignment.language, code))
        mode = "mock"
        llm_source = "mock"
    return parsed, mode, llm_source


def _latest_submissions(db: Session, user_id: int, assignment_ids: list[int]) -> dict[int, Submission]:
    if not assignment_ids:
        return {}
    rows = (
        db.query(Submission)
        .filter(Submission.user_id == user_id, Submission.assignment_id.in_(assignment_ids))
        .order_by(Submission.attempt.asc())
        .all()
    )
    return {row.assignment_id: row for row in rows}


@router.get("/courses/{course_id}/assignments")
def list_course_assignments(
    course_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None or course.status == "offline":
        raise HTTPException(status_code=404, detail="课程不存在或已下架")
    _ensure_enrolled(db, current, course)
    rows = (
        db.query(Assignment)
        .filter(Assignment.course_id == course_id, Assignment.status == "published")
        .order_by(Assignment.id.desc())
        .all()
    )
    latest = _latest_submissions(db, current.id, [row.id for row in rows])
    items = []
    for row in rows:
        submission = latest.get(row.id)
        items.append(
            _assignment_dict(
                row,
                submitted=_submission_dict(submission, include_code=False) if submission else None,
            )
        )
    return ok({"items": items, "total": len(items)})


@router.get("/assignments/{assignment_id}")
def assignment_detail(
    assignment_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.status != "published":
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_enrolled(db, current, course)
    return ok(_assignment_dict(assignment))


@router.post("/assignments/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    payload: SubmissionIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.status != "published":
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_enrolled(db, current, course)
    if assignment.deadline is not None and assignment.deadline < utcnow():
        raise HTTPException(status_code=400, detail="作业已截止，无法提交")

    if assignment.language == "python":
        cases = _loads(assignment.hidden_cases_json, []) or _loads(assignment.sample_cases_json, [])
        sandbox_result = sandbox.run_python_tests(payload.code, cases)
    else:
        sandbox_result = {
            "status": "not_executed",
            "available": False,
            "reason": "当前仅支持 Python 沙箱，其他语言仅做静态分析",
            "cases": [],
        }

    objective_score = None
    total = sandbox_result.get("total") or 0
    if sandbox_result.get("available") and total:
        objective_score = round((sandbox_result.get("passed") or 0) / total * 100, 1)

    ai_feedback, ai_mode, ai_source = _ai_review(
        assignment, payload.code, resolve_user_config(db, current)
    )
    try:
        ai_score = float(ai_feedback.get("score")) if ai_feedback.get("score") is not None else None
    except (TypeError, ValueError):
        ai_score = None

    last_attempt = (
        db.query(func.coalesce(func.max(Submission.attempt), 0))
        .filter(Submission.assignment_id == assignment.id, Submission.user_id == current.id)
        .scalar()
        or 0
    )
    submission = Submission(
        assignment_id=assignment.id,
        user_id=current.id,
        attempt=last_attempt + 1,
        code=payload.code,
        status=sandbox_result.get("status", "not_executed"),
        test_result_json=json.dumps(sandbox_result, ensure_ascii=False),
        objective_score=objective_score,
        ai_feedback_json=json.dumps(ai_feedback, ensure_ascii=False),
        ai_score=ai_score,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    data = _submission_dict(submission)
    data["sandbox"] = {
        "status": sandbox_result.get("status"),
        "available": bool(sandbox_result.get("available")),
        "reason": sandbox_result.get("reason", ""),
        "total": total,
    }
    data["ai_mode"] = ai_mode
    data["ai_source"] = ai_source
    data["assignment_title"] = assignment.title
    return ok(data, message="作业已提交")


@router.get("/users/me/submissions")
def my_submissions(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Submission, Assignment)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.user_id == current.id)
        .order_by(Submission.id.desc())
        .limit(50)
        .all()
    )
    items = []
    for submission, assignment in rows:
        item = _submission_dict(submission, include_code=False)
        item["assignment_title"] = assignment.title
        item["course_id"] = assignment.course_id
        items.append(item)
    return ok({"items": items, "total": len(items)})


@router.get("/submissions/{submission_id}")
def submission_detail(
    submission_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="提交不存在")
    assignment = db.get(Assignment, submission.assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if current.role == "student" and submission.user_id != current.id:
        raise HTTPException(status_code=404, detail="提交不存在")
    if current.role == "teacher":
        _ensure_course_access(course, current)
    data = _submission_dict(submission)
    data["assignment_title"] = assignment.title
    return ok(data)


@router.get("/admin/courses/{course_id}/assignments")
def admin_list_assignments(
    course_id: int,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    rows = (
        db.query(Assignment)
        .filter(Assignment.course_id == course_id)
        .order_by(Assignment.id.desc())
        .all()
    )
    items = [_assignment_dict(row, include_hidden=True) for row in rows]
    return ok({"items": items, "total": len(items)})


@router.post("/admin/courses/{course_id}/assignments")
def create_assignment(
    course_id: int,
    payload: AssignmentIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    if payload.chapter_id is not None:
        chapter = db.get(Chapter, payload.chapter_id)
        if chapter is None or chapter.course_id != course_id:
            raise HTTPException(status_code=400, detail="章节不属于该课程")
    assignment = Assignment(
        course_id=course_id,
        chapter_id=payload.chapter_id,
        title=payload.title.strip(),
        description=payload.description,
        language=payload.language,
        deadline=_parse_deadline(payload.deadline),
        rubric_json=json.dumps(payload.rubric or DEFAULT_RUBRIC, ensure_ascii=False),
        sample_cases_json=json.dumps(payload.sample_cases or [], ensure_ascii=False),
        hidden_cases_json=json.dumps(payload.hidden_cases or [], ensure_ascii=False),
        status=payload.status,
        created_by=current.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    audit.log(
        db,
        current,
        "assignment.create",
        "assignment",
        assignment.id,
        {"course_id": course_id, "title": assignment.title},
    )
    return ok(_assignment_dict(assignment, include_hidden=True), message="作业已创建")


@router.put("/admin/assignments/{assignment_id}")
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdateIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    data = payload.model_dump(exclude_unset=True)
    if data.get("chapter_id") is not None:
        chapter = db.get(Chapter, data["chapter_id"])
        if chapter is None or chapter.course_id != assignment.course_id:
            raise HTTPException(status_code=400, detail="章节不属于该课程")
    if "deadline" in data:
        assignment.deadline = _parse_deadline(data.pop("deadline"))
    for field in ("title", "description", "language", "status"):
        if field in data:
            setattr(assignment, field, data[field])
    if "rubric" in data:
        assignment.rubric_json = json.dumps(data["rubric"] or DEFAULT_RUBRIC, ensure_ascii=False)
    if "sample_cases" in data:
        assignment.sample_cases_json = json.dumps(data["sample_cases"] or [], ensure_ascii=False)
    if "hidden_cases" in data:
        assignment.hidden_cases_json = json.dumps(data["hidden_cases"] or [], ensure_ascii=False)
    if "chapter_id" in data:
        assignment.chapter_id = data["chapter_id"]
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    audit.log(db, current, "assignment.update", "assignment", assignment.id, {"fields": sorted(data.keys())})
    return ok(_assignment_dict(assignment, include_hidden=True), message="作业已更新")


@router.delete("/admin/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    title = assignment.title
    db.query(Submission).filter(Submission.assignment_id == assignment_id).delete(
        synchronize_session=False
    )
    db.delete(assignment)
    db.commit()
    audit.log(db, current, "assignment.delete", "assignment", assignment_id, {"title": title})
    return ok({"id": assignment_id}, message="作业已删除")


@router.get("/admin/assignments/{assignment_id}/submissions")
def admin_assignment_submissions(
    assignment_id: int,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    rows = (
        db.query(Submission, User)
        .join(User, Submission.user_id == User.id)
        .filter(Submission.assignment_id == assignment_id)
        .order_by(Submission.id.desc())
        .all()
    )
    items = []
    for submission, user in rows:
        item = _submission_dict(submission, include_code=False)
        item["user_name"] = user.nickname or user.username
        items.append(item)
    return ok({"items": items, "total": len(items)})


@router.patch("/admin/submissions/{submission_id}/review")
def review_submission(
    submission_id: int,
    payload: SubmissionReviewIn,
    current: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="提交不存在")
    assignment = db.get(Assignment, submission.assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    course = db.get(Course, assignment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_course_access(course, current)
    submission.final_score = payload.final_score
    submission.review_comment = payload.comment.strip()
    submission.reviewer_id = current.id
    submission.reviewed_at = utcnow()
    db.add(submission)
    db.commit()
    db.refresh(submission)
    audit.log(
        db,
        current,
        "submission.review",
        "submission",
        submission.id,
        {"final_score": submission.final_score},
    )
    return ok(_submission_dict(submission), message="复核已保存")