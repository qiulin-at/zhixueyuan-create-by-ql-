"""通知生成逻辑。

两类触发来源：
1. 事件驱动（实时）：收藏的课程有新评价 / 被下架 —— 在对应写接口里直接调用；
2. 登录/拉取时驱动（幂等）：学习进度停滞超过 STALE_DAYS 天 —— 由 dedup_key 去重，不会重复轰炸。

说明：本项目暂无「学习计划」实体，指导书里的「学习计划到期」以「学习进度停滞提醒」等价实现。
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from ..models import Course, Favorite, LearningRecord, Notification, User, utcnow

logger = logging.getLogger("zhixueyun.notification")

STALE_DAYS = 7
MAX_PER_RUN = 20
TITLE_LIMIT = 120


def push(
    db: Session,
    user_id: int,
    type_: str,
    title: str,
    content: str = "",
    link: str = "",
    dedup_key: str | None = None,
) -> Notification | None:
    """写一条通知；带 dedup_key 时同一用户同 key 只保留一条。"""
    if dedup_key:
        exists = (
            db.query(Notification.id)
            .filter(Notification.user_id == user_id, Notification.dedup_key == dedup_key)
            .first()
        )
        if exists is not None:
            return None
    item = Notification(
        user_id=user_id,
        type=type_,
        title=title[:TITLE_LIMIT],
        content=content,
        link=link,
        dedup_key=dedup_key,
    )
    db.add(item)
    return item


def notify_course_comment(db: Session, course: Course, comment_id: int, actor_id: int | None = None) -> int:
    """课程有新评价：通知所有收藏了该课程的用户（跳过评论者本人）。"""
    rows = db.query(Favorite.user_id).filter(Favorite.course_id == course.id).all()
    created = 0
    for (user_id,) in rows:
        if actor_id is not None and user_id == actor_id:
            continue
        item = push(
            db,
            user_id,
            "course_update",
            f"你收藏的《{course.title}》有新评价",
            f"最新评分 {round(course.rating, 1)}，累计 {course.rating_count} 条评价，点击查看详情。",
            f"/courses/{course.id}",
            dedup_key=f"comment:{comment_id}",
        )
        if item is not None:
            created += 1
    return created


def notify_course_offline(db: Session, course: Course, actor_id: int | None = None) -> int:
    """课程被下架：通知收藏了该课程的用户。每次状态变更都是一次独立事件，不做去重。"""
    rows = db.query(Favorite.user_id).filter(Favorite.course_id == course.id).all()
    created = 0
    for (user_id,) in rows:
        if actor_id is not None and user_id == actor_id:
            continue
        item = push(
            db,
            user_id,
            "course_update",
            f"你收藏的《{course.title}》已下架",
            "课程暂时不可学习，恢复上架后会再次开放，你可以先学习其他课程。",
            f"/courses/{course.id}",
        )
        if item is not None:
            created += 1
    return created


def generate_notifications(db: Session, user: User) -> int:
    """按当前数据补齐应得的通知（目前是学习停滞提醒），幂等。"""
    now = utcnow()
    threshold = now - timedelta(days=STALE_DAYS)
    rows = (
        db.query(LearningRecord, Course)
        .join(Course, LearningRecord.course_id == Course.id)
        .filter(
            LearningRecord.user_id == user.id,
            LearningRecord.progress < 100,
            LearningRecord.updated_at < threshold,
        )
        .order_by(LearningRecord.updated_at.asc())
        .limit(MAX_PER_RUN)
        .all()
    )

    created = 0
    for record, course in rows:
        days = max((now - record.updated_at).days, STALE_DAYS)
        item = push(
            db,
            user.id,
            "study_reminder",
            f"《{course.title}》已经 {days} 天没学习了",
            f"当前进度 {record.progress}%，建议今天花 20 分钟继续，保持学习节奏。",
            f"/courses/{course.id}",
            dedup_key=f"stale:{record.id}:{record.updated_at.date().isoformat()}",
        )
        if item is not None:
            created += 1

    if created:
        db.commit()
        logger.info("为用户 %s 生成 %s 条学习提醒", user.username, created)
    return created
