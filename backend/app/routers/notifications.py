import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..deps import get_current_user, get_db
from ..models import Notification, User, utcnow
from ..security import decode_access_token
from ..services.notifications import generate_notifications
from ..utils import ok, paginated

logger = logging.getLogger("zhixueyun.notification")
router = APIRouter(prefix="/api/notifications", tags=["通知"])


def _item(item: Notification) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "title": item.title,
        "content": item.content,
        "link": item.link,
        "is_read": bool(item.is_read),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user_id, Notification.is_read == 0)
        .scalar()
        or 0
    )


def _safe_generate(db: Session, current: User) -> None:
    """补齐应得通知；任何异常都不能影响主流程（登录/列表）。"""
    try:
        generate_notifications(db, current)
    except Exception:
        db.rollback()
        logger.exception("生成通知失败，已忽略 user_id=%s", current.id)


async def notification_event_stream(request: Request, user_id: int, interval: float = 15.0):
    while True:
        if await request.is_disconnected():
            break
        with SessionLocal() as db:
            unread = _unread_count(db, user_id)
        payload = {"unread": unread, "ts": utcnow().isoformat()}
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        await asyncio.sleep(interval)


@router.get("/stream")
async def stream_notifications(request: Request, token: str | None = Query(default=None)):
    if not token:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录") from None
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    return StreamingResponse(
        notification_event_stream(request, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/unread-count")
def unread_count(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _safe_generate(db, current)
    return ok({"unread": _unread_count(db, current.id)})


@router.get("")
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    unread_only: bool = False,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _safe_generate(db, current)
    query = db.query(Notification).filter(Notification.user_id == current.id)
    if unread_only:
        query = query.filter(Notification.is_read == 0)
    total = query.count()
    rows = query.order_by(Notification.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ok(paginated([_item(item) for item in rows], total, page, page_size))


@router.post("/read-all")
def read_all(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current.id, Notification.is_read == 0)
        .update({Notification.is_read: 1}, synchronize_session=False)
    )
    db.commit()
    return ok({"updated": updated, "unread": 0}, message="已全部标记为已读")


@router.post("/{notification_id}/read")
def read_one(
    notification_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="通知不存在")
    if not item.is_read:
        item.is_read = 1
        db.add(item)
        db.commit()
    return ok({"id": item.id, "is_read": True, "unread": _unread_count(db, current.id)}, message="已标记为已读")
