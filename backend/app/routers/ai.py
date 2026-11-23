import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import AiConversation, AiMessage, Chapter, Course, LearningRecord, User
from ..schemas import ChatIn, GradeIn, LearningPathIn, ReportIn
from ..services.llm import llm_gateway
from ..services.mock_engine import mock_answer, mock_grade, mock_learning_path, mock_study_report
from ..services.prompts import GRADE_SYSTEM, LEARNING_PATH_SYSTEM, REPORT_SYSTEM, TUTOR_SYSTEM
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
    system_prompt = TUTOR_SYSTEM.format(
        course_title=course_title,
        course_intro=course_intro or "暂无简介",
        chapter_title=chapter_title,
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": item.role, "content": item.content} for item in history)
    answer = llm_gateway.chat(messages, temperature=0.6, max_tokens=900)
    mode = "online"
    if answer is None:
        answer = mock_answer(payload.message, course_title, chapter_title)
        mode = "mock"
    db.add(AiMessage(conversation_id=conversation.id, role="assistant", content=answer))
    db.commit()
    return ok(
        {
            "conversation_id": conversation.id,
            "course_id": conversation.course_id,
            "answer": answer,
            "mode": mode,
        }
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
                }
                for item in messages
            ],
        }
    )


@router.post("/learning-path")
def learning_path(payload: LearningPathIn, current: User = Depends(get_current_user)):
    prompt = LEARNING_PATH_SYSTEM.format(
        goal=payload.goal,
        weekly_hours=payload.weekly_hours,
        weak_points=payload.weak_points.strip() or "未填写",
    )
    content = llm_gateway.chat(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请为「{payload.goal}」制定学习路径"},
        ],
        temperature=0.5,
        max_tokens=1200,
    )
    mode = "online"
    if content is None:
        content = mock_learning_path(payload.goal, payload.weekly_hours, payload.weak_points)
        mode = "mock"
    return ok({"content": content, "mode": mode})


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


@router.post("/study-report")
def study_report(payload: ReportIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (
        db.query(LearningRecord, Course)
        .join(Course, LearningRecord.course_id == Course.id)
        .filter(LearningRecord.user_id == current.id)
        .all()
    )
    total_minutes = sum(record.study_minutes for record, _ in records)
    course_count = len(records)
    avg_progress = round(sum(record.progress for record, _ in records) / course_count) if course_count else 0
    weakest = min(records, key=lambda item: item[0].progress) if records else None
    weak_points = f"《{weakest[1].title}》进度仅 {weakest[0].progress}%" if weakest is not None else ""
    stats = {
        "total_minutes": total_minutes,
        "course_count": course_count,
        "avg_progress": avg_progress,
        "weak_points": weak_points,
    }
    period_label = "本周" if payload.period == "week" else "本月"
    prompt = REPORT_SYSTEM.format(period_label=period_label, **stats)
    content = llm_gateway.chat(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请生成学习报告"},
        ],
        temperature=0.6,
        max_tokens=1000,
    )
    mode = "online"
    if content is None:
        content = mock_study_report(stats)
        mode = "mock"
    return ok({"content": content, "mode": mode, "stats": stats, "period": payload.period})