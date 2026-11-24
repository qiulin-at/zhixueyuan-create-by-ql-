import json
import logging

from sqlalchemy.orm import Session

from ..models import OperationLog, User

logger = logging.getLogger("zhixueyun.audit")


def log(
    db: Session,
    actor: User,
    action: str,
    target_type: str,
    target_id: int | None = None,
    detail: dict | None = None,
) -> None:
    """记录后台写操作；失败只写应用日志，不影响业务结果。"""
    try:
        db.add(
            OperationLog(
                actor_id=actor.id,
                actor_role=actor.role,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=json.dumps(detail or {}, ensure_ascii=False),
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("写操作日志失败：action=%s target=%s/%s", action, target_type, target_id)