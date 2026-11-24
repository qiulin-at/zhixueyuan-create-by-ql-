import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import (
    AiConversation,
    AiFeedback,
    AiMessage,
    Assignment,
    Chapter,
    Course,
    LearningEvent,
    LearningPath,
    LearningRecord,
    Submission,
    User,
)
from ..schemas import ChatIn, FeedbackIn, GradeIn, LearningPathActionIn, LearningPathIn, ReportIn
from ..services.llm import llm_gateway
from ..services.mock_engine import mock_answer, mock_grade, mock_learning_path_structured, mock_study_report
from ..services.prompts import GRADE_SYSTEM, LEARNING_PATH_JSON_SYSTEM, REPORT_SYSTEM, TUTOR_SYSTEM
from ..services.rag import format_materials, format_reference_line, retrieve_materials
from ..utils import ok

logger = logging.getLogger("zhixueyun.ai")
router = APIRouter(prefix="/api/ai", tags=["AI 学习助手"])


def _chapter_context(db: Session, user: User, course: Course | None) -> str:
    if course is None:
        return "综合答疑"
    record = (
        db.query(LearningRecord)
        .filter(LearningRecord.user_id == user.id, LearningRecord.course_id == course.id)
        .first()
    )
    if record is not None and record.last_chapter_id:
        chapter = db.get(Chapter, record.last_chapter_id)
        if chapter is not None:
            return chapter.title
    first = db.query(Chapter).filter(Chapter.course_id == course.id).order_by(Chapter.sort.asc()).first()
    return first.title if first else "课程导学"


@router.post("/chat")
def chat(payload: ChatIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = None
    if payload.conversation_id is not None:
        conversation = (
            db.query(AiConversation)
            .filter(AiConversation.id == payload.conversation_id, AiConversation.user_id == current.id)
            .first()
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="会话不存在")
    course = db.get(Course, payload.course_id) if payload.course_id else None
    if conversation is None:
        conversation = AiConversation(
            user_id=current.id,
            course_id=course.id if course is not None else None,
            title=payload.message.strip()[:30] or "新的对话",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    elif conversation.course_id and course is None:
        course = db.get(Course, conversation.course_id)

    db.add(AiMessage(conversation_id=conversation.id, role="user", content=payload.message))
    db.commit()

    history = (
        db.query(AiMessage)
        .filter(AiMessage.conversation_id == conversation.id)
        .order_by(AiMessage.id.desc())
        .limit(10)
        .all()
    )
    history.reverse()
    course_title = course.title if course is not None else "通识学习"
    course_intro = course.intro if course is not None else "平台通识课程与学习方法"
    chapter_title = _chapter_context(db, current, course)
    materials = retrieve_materials(db, course.id, payload.message, top_k=3) if course is not None else []
    insufficient = course is not None and not materials
    system_prompt = TUTOR_SYSTEM.format(
        course_title=course_title,
        course_intro=course_intro or "暂无简介",
        chapter_title=chapter_title,
        materials=format_materials(materials),
    )
    if insufficient:
        system_prompt += (
            "\n注意：本次检索到的课程资料为空。必须明确说明「课程资料暂未覆盖」，"
            "再基于通用知识给出解释；禁止编造课程要求、评分标准或资料来源。"
        )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": item.role, "content": item.content} for item in history)
    answer = llm_gateway.chat(messages, temperature=0.6, max_tokens=900)
    mode = "online"
    if answer is None:
        answer = mock_answer(payload.message, course_title, chapter_title)
        mode = "mock"
    if insufficient:
        prefix = "课程资料暂未覆盖该问题，以下为通用解释：\n\n"
        if not answer.startswith(prefix):
            answer = prefix + answer
    elif materials and "参考：" not in answer:
        reference = format_reference_line(course_title, materials)
        if reference:
            answer = f"{answer.rstrip()}\n\n{reference}"
    assistant = AiMessage(conversation_id=conversation.id, role="assistant", content=answer)
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    citations = [
        {
            "material_id": item["material_id"],
            "title": item["title"],
            "section": item["section"],
            "chapter_title": item["chapter_title"],
            "snippet": item["snippet"],
            "score": item["score"],
        }
        for item in materials
    ]
    return ok(
        {
            "conversation_id": conversation.id,
            "course_id": conversation.course_id,
            "message_id": assistant.id,
            "answer": answer,
            "mode": mode,
            "insufficient": insufficient,
            "citations": citations,
            "references": format_reference_line(course_title, materials) if materials else "",
        }
    )


@router.post("/messages/{message_id}/feedback")
def submit_feedback(
    message_id: int,
    payload: FeedbackIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = db.get(AiMessage, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="只能对 AI 回答提交反馈")
    conversation = db.get(AiConversation, message.conversation_id)
    if conversation is None or conversation.user_id != current.id:
        raise HTTPException(status_code=404, detail="消息不存在")
    feedback = (
        db.query(AiFeedback)
        .filter(AiFeedback.message_id == message_id, AiFeedback.user_id == current.id)
        .first()
    )
    if feedback is None:
        feedback = AiFeedback(
            message_id=message_id,
            user_id=current.id,
            helpful=1 if payload.helpful else 0,
            reason=payload.reason.strip(),
        )
        db.add(feedback)
    else:
        feedback.helpful = 1 if payload.helpful else 0
        feedback.reason = payload.reason.strip()
        db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return ok(
        {
            "message_id": message_id,
            "helpful": bool(feedback.helpful),
            "reason": feedback.reason,
        },
        message="反馈已记录",
    )


@router.get("/conversations")
def list_conversations(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(AiConversation)
        .filter(AiConversation.user_id == current.id)
        .order_by(AiConversation.id.desc())
        .limit(50)
        .all()
    )
    items = []
    for conversation in rows:
        course = db.get(Course, conversation.course_id) if conversation.course_id else None
        items.append(
            {
                "id": conversation.id,
                "title": conversation.title,
                "course_id": conversation.course_id,
                "course_title": course.title if course is not None else "通识答疑",
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            }
        )
    return ok({"items": items, "total": len(items)})


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(AiConversation)
        .filter(AiConversation.id == conversation_id, AiConversation.user_id == current.id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = (
        db.query(AiMessage)
        .filter(AiMessage.conversation_id == conversation.id)
        .order_by(AiMessage.id.asc())
        .all()
    )
    message_ids = [item.id for item in messages]
    feedbacks = (
        {
            feedback.message_id: feedback
            for feedback in db.query(AiFeedback)
            .filter(AiFeedback.user_id == current.id, AiFeedback.message_id.in_(message_ids))
            .all()
        }
        if message_ids
        else {}
    )
    course = db.get(Course, conversation.course_id) if conversation.course_id else None
    return ok(
        {
            "id": conversation.id,
            "title": conversation.title,
            "course_id": conversation.course_id,
            "course_title": course.title if course is not None else "通识答疑",
            "messages": [
                {
                    "id": item.id,
                    "role": item.role,
                    "content": item.content,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "citations": [],
                    "insufficient": False,
                    "feedback": (
                        "helpful"
                        if feedbacks[item.id].helpful
                        else "unhelpful"
                    )
                    if item.id in feedbacks
                    else None,
                }
                for item in messages
            ],
        }
    )


def _published_courses(db: Session) -> list[Course]:
    return (
        db.query(Course)
        .filter(Course.status == "published", Course.review_status == "published")
        .order_by(Course.study_count.desc(), Course.id.asc())
        .all()
    )


def _learning_snapshot(db: Session, user: User, weak_points: str = "") -> dict:
    records = db.query(LearningRecord).filter(LearningRecord.user_id == user.id).all()
    items = []
    for record in records:
        course = db.get(Course, record.course_id)
        if course is None:
            continue
        items.append(
            {
                "course_id": course.id,
                "title": course.title,
                "progress": record.progress,
                "last_chapter_id": record.last_chapter_id,
                "effective_minutes": record.effective_minutes,
            }
        )
    return {
        "records": items,
        "completed_courses": [item for item in items if item["progress"] >= 100],
        "weak_points": weak_points.strip(),
    }


def _parse_json_payload(content: str | None) -> dict | None:
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


def _normalize_stages(raw_stages, course_map: dict[int, Course], strict: bool = False):
    stages = []
    gaps = []
    for index, stage in enumerate((raw_stages or [])[:4], start=1):
        if not isinstance(stage, dict):
            continue
        courses = []
        for item in (stage.get("courses") or [])[:4]:
            if not isinstance(item, dict):
                continue
            try:
                course_id = int(item.get("course_id", 0))
            except (TypeError, ValueError):
                course_id = 0
            if course_id in course_map:
                course = course_map[course_id]
                try:
                    hours = int(item.get("hours") or 4)
                except (TypeError, ValueError):
                    hours = 4
                courses.append(
                    {
                        "course_id": course.id,
                        "title": course.title,
                        "chapters": [str(chapter)[:20] for chapter in (item.get("chapters") or [])[:8]],
                        "hours": max(1, min(hours, 40)),
                    }
                )
            else:
                gaps.append(f"平台无课程：{item.get('title') or course_id}")
        if strict and not courses and stage.get("courses"):
            raise HTTPException(status_code=400, detail="调整后的路径包含平台不存在的课程")
        stages.append(
            {
                "stage": index,
                "goal": str(stage.get("goal") or f"阶段 {index}")[:120],
                "courses": courses,
                "checkpoint": str(stage.get("checkpoint") or "")[:200],
                "reason": str(stage.get("reason") or "")[:300],
            }
        )
    return stages, "；".join(gaps)


def _render_path_markdown(path: dict) -> str:
    lines = [
        f"## 学习路径：{path['goal']}",
        "",
        f"每周投入：**{path['weekly_hours']} 小时**",
        "",
        "| 阶段 | 目标 | 课程 | 检查点 |",
        "|---|---|---|---|",
    ]
    for stage in path.get("stages", []):
        courses = "、".join(item["title"] for item in stage["courses"]) or "—"
        lines.append(
            f"| 阶段 {stage['stage']} | {stage['goal']} | {courses} | {stage['checkpoint']} |"
        )
    if path.get("resource_gap"):
        lines.extend(["", f"**资源缺口：** {path['resource_gap']}"])
    return "\n".join(lines)


def _path_dict(path: LearningPath) -> dict:
    try:
        stages = json.loads(path.stages_json or "[]")
    except (TypeError, ValueError):
        stages = []
    try:
        inputs = json.loads(path.inputs_json or "{}")
    except (TypeError, ValueError):
        inputs = {}
    return {
        "id": path.id,
        "goal": path.goal,
        "weekly_hours": path.weekly_hours,
        "stages": stages,
        "resource_gap": path.resource_gap,
        "inputs": inputs,
        "status": path.status,
        "version": path.version,
        "source": path.source,
        "created_at": path.created_at.isoformat() if path.created_at else None,
        "updated_at": path.updated_at.isoformat() if path.updated_at else None,
    }


@router.post("/learning-path")
def learning_path(
    payload: LearningPathIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    courses = _published_courses(db)
    course_map = {course.id: course for course in courses}
    snapshot = _learning_snapshot(db, current, payload.weak_points)
    available = [
        {
            "course_id": course.id,
            "title": course.title,
            "tech_system": course.tech_system,
            "tech_direction": course.tech_direction,
            "level": course.level,
        }
        for course in courses
    ]
    prompt = LEARNING_PATH_JSON_SYSTEM.format(
        goal=payload.goal,
        weekly_hours=payload.weekly_hours,
        records=json.dumps(snapshot["records"], ensure_ascii=False),
        completed_courses=json.dumps(snapshot["completed_courses"], ensure_ascii=False),
        available_courses=json.dumps(available, ensure_ascii=False),
    )
    content = llm_gateway.chat(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请为「{payload.goal}」生成路径 JSON"},
        ],
        temperature=0.4,
        max_tokens=1600,
    )
    mode = "online"
    raw = _parse_json_payload(content)
    if raw is None:
        raw = mock_learning_path_structured(payload.goal, payload.weekly_hours, available, snapshot)
        mode = "mock"
    stages, gaps = _normalize_stages(raw.get("stages") or [], course_map)
    resource_gap = "；".join(
        part for part in [(raw.get("resource_gap") or "").strip(), gaps] if part
    )
    path = LearningPath(
        user_id=current.id,
        goal=payload.goal.strip(),
        weekly_hours=payload.weekly_hours,
        stages_json=json.dumps(stages, ensure_ascii=False),
        resource_gap=resource_gap,
        inputs_json=json.dumps(snapshot, ensure_ascii=False),
        status="draft",
        version=1,
        source=mode,
    )
    db.add(path)
    db.commit()
    db.refresh(path)
    data = _path_dict(path)
    data["content"] = _render_path_markdown(data)
    data["mode"] = mode
    return ok(data, message="学习路径已生成")


@router.get("/learning-paths")
def list_learning_paths(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(LearningPath)
        .filter(LearningPath.user_id == current.id)
        .order_by(LearningPath.id.desc())
        .limit(20)
        .all()
    )
    items = [_path_dict(row) for row in rows]
    return ok({"items": items, "total": len(items)})


@router.patch("/learning-paths/{path_id}")
def update_learning_path(
    path_id: int,
    payload: LearningPathActionIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    path = db.get(LearningPath, path_id)
    if path is None or path.user_id != current.id:
        raise HTTPException(status_code=404, detail="学习路径不存在")
    if payload.action == "accept":
        path.status = "active"
    elif payload.action == "reject":
        path.status = "rejected"
    else:
        course_map = {course.id: course for course in _published_courses(db)}
        try:
            existing = json.loads(path.stages_json or "[]")
        except (TypeError, ValueError):
            existing = []
        normalized, _ = _normalize_stages(
            payload.stages if payload.stages is not None else existing,
            course_map,
            strict=True,
        )
        path.stages_json = json.dumps(normalized, ensure_ascii=False)
        path.status = "adjusted"
        path.version = (path.version or 1) + 1
    db.add(path)
    db.commit()
    db.refresh(path)
    return ok(_path_dict(path), message="学习路径已更新")


@router.post("/grade")
def grade(payload: GradeIn, current: User = Depends(get_current_user)):
    prompt = GRADE_SYSTEM.format(title=payload.title, language=payload.language)
    content = llm_gateway.chat(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": payload.code},
        ],
        temperature=0.2,
        max_tokens=1200,
        json_mode=True,
    )
    mode = "online"
    parsed = None
    if content is not None:
        try:
            parsed = json.loads(content)
        except ValueError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end > start:
                try:
                    parsed = json.loads(content[start : end + 1])
                except ValueError:
                    parsed = None
    if parsed is None:
        parsed = json.loads(mock_grade(payload.title, payload.language, payload.code))
        mode = "mock"
    return ok({"result": parsed, "mode": mode})


def _report_window(period: str):
    days = 7 if period == "week" else 30
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    previous_end = start
    previous_start = previous_end - timedelta(days=days)
    return start, end, previous_start, previous_end


def _collect_period_stats(db: Session, user_id: int, start: datetime, end: datetime):
    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.user_id == user_id,
            LearningEvent.occurred_at >= start,
            LearningEvent.occurred_at < end,
        )
        .all()
    )
    heartbeat_seconds = sum(
        event.duration_sec for event in events if event.event_type == "heartbeat"
    )
    completed = {
        event.chapter_id
        for event in events
        if event.event_type == "complete_chapter" and event.chapter_id is not None
    }
    active_days = {event.occurred_at.date() for event in events if event.occurred_at}
    event_course_ids = {event.course_id for event in events}

    submissions = (
        db.query(Submission)
        .filter(
            Submission.user_id == user_id,
            Submission.submitted_at >= start,
            Submission.submitted_at < end,
        )
        .all()
    )
    scores = []
    dimensions: dict[str, list[float]] = {}
    for submission in submissions:
        score = submission.final_score if submission.final_score is not None else submission.ai_score
        if score is not None:
            scores.append(float(score))
        feedback = _parse_json_payload(submission.ai_feedback_json)
        dimension_scores = feedback.get("dimension_scores") or {}
        if isinstance(dimension_scores, dict):
            for name, value in dimension_scores.items():
                try:
                    dimensions.setdefault(str(name), []).append(float(value))
                except (TypeError, ValueError):
                    continue

    return (
        {
            "effective_minutes": round(heartbeat_seconds / 60),
            "chapters_completed": len(completed),
            "active_days": len(active_days),
            "course_count": len(event_course_ids),
            "submission_count": len(submissions),
            "avg_assignment_score": round(sum(scores) / len(scores), 1) if scores else None,
        },
        event_course_ids,
        [
            {
                "dimension": name,
                "name": name,
                "score": round(sum(values) / len(values), 1),
                "samples": len(values),
            }
            for name, values in dimensions.items()
        ],
    )


def _merge_delta(current: dict, previous: dict) -> dict:
    return {
        "effective_minutes": current["effective_minutes"] - previous["effective_minutes"],
        "chapters_completed": current["chapters_completed"] - previous["chapters_completed"],
        "active_days": current["active_days"] - previous["active_days"],
        "course_count": current["course_count"] - previous["course_count"],
        "avg_assignment_score": (
            round(current["avg_assignment_score"] - previous["avg_assignment_score"], 1)
            if current["avg_assignment_score"] is not None
            and previous["avg_assignment_score"] is not None
            else None
        ),
    }


@router.post("/study-report")
def study_report(
    payload: ReportIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end, previous_start, previous_end = _report_window(payload.period)
    current_stats, event_course_ids, knowledge = _collect_period_stats(
        db, current.id, start, end
    )
    previous_stats, _, _ = _collect_period_stats(db, current.id, previous_start, previous_end)

    learning_course_ids = {
        record.course_id
        for record in db.query(LearningRecord)
        .filter(LearningRecord.user_id == current.id, LearningRecord.progress > 0)
        .all()
    }
    scope_ids = event_course_ids | learning_course_ids
    courses = (
        db.query(Course).filter(Course.id.in_(scope_ids)).order_by(Course.id.asc()).all()
        if scope_ids
        else []
    )
    course_scope = [{"course_id": course.id, "title": course.title} for course in courses]
    current_stats["course_count"] = len(course_scope) or current_stats["course_count"]
    delta = _merge_delta(current_stats, previous_stats)

    weakest = min(knowledge, key=lambda item: item["score"]) if knowledge else None
    weak_points = (
        f"{weakest['name']}得分 {weakest['score']}"
        if weakest is not None
        else ("暂无作业数据，建议先完成一次作业" if not knowledge else "")
    )
    period_label = "本周" if payload.period == "week" else "本月"
    prompt = REPORT_SYSTEM.format(
        period_label=period_label,
        total_minutes=current_stats["effective_minutes"],
        course_count=current_stats["course_count"],
        avg_progress=current_stats["avg_assignment_score"] or 0,
        weak_points=weak_points,
    )
    prompt += (
        "\n注意：以下统计数字由系统计算，禁止新增或修改任何数字；"
        "建议必须指向具体课程、章节或作业。"
    )
    analysis = llm_gateway.chat(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请基于给定统计生成学习报告分析"},
        ],
        temperature=0.5,
        max_tokens=1000,
    )
    mode = "online"
    if analysis is None:
        analysis = mock_study_report(
            {
                "total_minutes": current_stats["effective_minutes"],
                "course_count": current_stats["course_count"],
                "avg_progress": current_stats["avg_assignment_score"] or 0,
                "weak_points": weak_points,
            }
        )
        mode = "mock"

    content = (
        f"## {period_label}学习报告\n\n"
        f"- 有效学习：**{current_stats['effective_minutes']} 分钟**"
        f"（环比 {delta['effective_minutes']:+d}）\n"
        f"- 完成章节：**{current_stats['chapters_completed']}** 章"
        f"（环比 {delta['chapters_completed']:+d}）\n"
        f"- 活跃天数：**{current_stats['active_days']}** 天\n"
        f"- 作业平均分：**{current_stats['avg_assignment_score'] if current_stats['avg_assignment_score'] is not None else '暂无'}**\n\n"
        f"### AI 分析\n{analysis}"
    )
    return ok(
        {
            "period": payload.period,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "previous_range": {"start": previous_start.isoformat(), "end": previous_end.isoformat()},
            "updated_at": end.isoformat(),
            "course_scope": course_scope,
            "stats": {**current_stats, "previous": previous_stats, "delta": delta},
            "knowledge": knowledge,
            "analysis": analysis,
            "content": content,
            "mode": mode,
        }
    )