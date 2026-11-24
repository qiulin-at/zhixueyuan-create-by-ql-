from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Course, Favorite, LearningRecord, Order, User, UserLLMConfig, utcnow
from ..schemas import LLMConfigIn, UserOut, UserUpdateIn
from ..security import hash_password
from ..services.llm import llm_gateway
from ..services.user_llm import config_public, resolve_user_config, save_config
from ..utils import ok

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me")
def get_me(current: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(current).model_dump())


@router.put("/me")
def update_me(
    payload: UserUpdateIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.nickname is not None:
        current.nickname = payload.nickname.strip()
    if payload.avatar is not None:
        current.avatar = payload.avatar.strip()
    if payload.major is not None:
        current.major = payload.major.strip()
    if payload.password is not None:
        current.hashed_password = hash_password(payload.password)
    db.add(current)
    db.commit()
    db.refresh(current)
    return ok(UserOut.model_validate(current).model_dump(), message="资料已更新")


@router.get("/me/favorites")
def list_favorites(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Favorite, Course)
        .join(Course, Favorite.course_id == Course.id)
        .filter(Favorite.user_id == current.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    items = [
        {
            "id": course.id,
            "title": course.title,
            "cover": course.cover,
            "tech_system": course.tech_system,
            "tech_direction": course.tech_direction,
            "level": course.level,
            "is_free": bool(course.is_free),
            "rating": round(course.rating, 1),
            "study_count": course.study_count,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None,
        }
        for fav, course in rows
    ]
    return ok({"items": items, "total": len(items)})


@router.get("/me/learning")
def list_learning(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(LearningRecord, Course)
        .join(Course, LearningRecord.course_id == Course.id)
        .filter(LearningRecord.user_id == current.id)
        .order_by(LearningRecord.updated_at.desc())
        .all()
    )
    items = [
        {
            "course_id": course.id,
            "title": course.title,
            "cover": course.cover,
            "tech_system": course.tech_system,
            "progress": record.progress,
            "study_minutes": record.study_minutes,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }
        for record, course in rows
    ]
    total_minutes = sum(item["study_minutes"] for item in items)
    return ok(
        {
            "items": items,
            "total": len(items),
            "total_minutes": total_minutes,
            "avg_progress": round(sum(item["progress"] for item in items) / len(items)) if items else 0,
        }
    )


@router.get("/me/orders")
def list_orders(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Order, Course)
        .join(Course, Order.course_id == Course.id)
        .filter(Order.user_id == current.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    items = [
        {
            "id": order.id,
            "order_no": order.order_no,
            "course_id": course.id,
            "title": course.title,
            "cover": course.cover,
            "amount": round(float(order.amount), 2),
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        for order, course in rows
    ]
    return ok(
        {
            "items": items,
            "total": len(items),
            "total_amount": round(sum(item["amount"] for item in items), 2),
        }
    )

@router.get("/me/llm-config")
def get_llm_config(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == current.id).first()
    if config is None:
        return ok(
            {
                "configured": False,
                "enabled": False,
                "provider": "",
                "base_url": "",
                "model": "",
                "masked_key": "",
                "last_tested_at": None,
                "last_test_ok": None,
            }
        )
    return ok(config_public(config))


@router.put("/me/llm-config")
def update_llm_config(
    payload: LLMConfigIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        config = save_config(
            db,
            current,
            payload.provider,
            payload.base_url,
            payload.model,
            payload.api_key,
            payload.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok(config_public(config), message="模型配置已保存")


@router.delete("/me/llm-config")
def delete_llm_config(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == current.id).first()
    if config is not None:
        db.delete(config)
        db.commit()
    return ok({"configured": False}, message="模型配置已清除")


@router.post("/me/llm-config/test")
def test_llm_config(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = resolve_user_config(db, current)
    if config is None:
        raise HTTPException(status_code=400, detail="请先保存并启用模型配置")
    passed, message = llm_gateway.test_user_config(config)
    record = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == current.id).first()
    if record is not None:
        record.last_tested_at = utcnow()
        record.last_test_ok = 1 if passed else 0
        db.add(record)
        db.commit()
    if not passed:
        raise HTTPException(status_code=400, detail=message)
    return ok({"ok": True, "message": message})