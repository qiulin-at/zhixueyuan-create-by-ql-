import logging
import random
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models import PasswordResetCode, User
from ..schemas import AuthOut, LoginIn, RegisterIn, ResetPasswordIn, SendCodeIn, UserOut
from ..security import create_access_token, hash_password, verify_password
from ..services.notifications import generate_notifications, push
from ..utils import ok

logger = logging.getLogger("zhixueyun.auth")
router = APIRouter(prefix="/api/auth", tags=["认证"])

CODE_TTL_MINUTES = 10


def _utcnow() -> datetime:
    """与 models.utcnow 保持一致：存 naive UTC，避免 datetime.utcnow() 的弃用告警。"""
    return datetime.now(UTC).replace(tzinfo=None)


def _token_payload(user: User) -> dict:
    token = create_access_token(user.id, user.role)
    return AuthOut(access_token=token, user=UserOut.model_validate(user)).model_dump()


@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if "@" not in payload.email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    exists = (
        db.query(User)
        .filter(or_(User.username == payload.username, User.email == payload.email))
        .first()
    )
    if exists is not None:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被注册")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        nickname=payload.nickname.strip() or payload.username,
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        push(
            db,
            user.id,
            "system",
            "欢迎加入智学云",
            "从课程中心挑一门课开始，AI 学习助手会结合你的学习进度答疑并生成学习路径。",
            "/",
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("生成欢迎通知失败，已忽略 user_id=%s", user.id)
    return ok(_token_payload(user), message="注册成功")


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    account = payload.account.strip()
    user = db.query(User).filter(or_(User.username == account, User.email == account)).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="账号或密码不正确")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被停用，请联系管理员")
    try:
        generate_notifications(db, user)
    except Exception:
        db.rollback()
        logger.exception("登录时生成学习提醒失败，已忽略 user_id=%s", user.id)
    return ok(_token_payload(user), message="登录成功")


@router.post("/send-code")
def send_code(payload: SendCodeIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="该邮箱尚未注册")
    code = f"{random.randint(0, 999999):06d}"
    # 同一邮箱的旧验证码全部作废，只保留最新一条（落库，重启/多 worker 均可用）
    db.query(PasswordResetCode).filter(
        PasswordResetCode.email == payload.email,
        PasswordResetCode.used == 0,
    ).update({PasswordResetCode.used: 1}, synchronize_session=False)
    db.add(
        PasswordResetCode(
            email=payload.email,
            code=code,
            expires_at=_utcnow() + timedelta(minutes=CODE_TTL_MINUTES),
        )
    )
    db.commit()
    logger.info("邮箱 %s 的演示验证码：%s", payload.email, code)
    return ok(
        {"expires_in": CODE_TTL_MINUTES * 60, "demo_code": code},
        message="验证码已生成（演示环境直接返回，生产环境应发送邮件）",
    )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    record = (
        db.query(PasswordResetCode)
        .filter(PasswordResetCode.email == payload.email, PasswordResetCode.used == 0)
        .order_by(PasswordResetCode.id.desc())
        .first()
    )
    if record is None:
        raise HTTPException(status_code=400, detail="请先获取验证码")
    if _utcnow() > record.expires_at:
        record.used = 1
        db.commit()
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if record.code != payload.code.strip():
        raise HTTPException(status_code=400, detail="验证码不正确")
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="该邮箱尚未注册")
    user.hashed_password = hash_password(payload.new_password)
    record.used = 1
    db.commit()
    return ok(message="密码已重置，请使用新密码登录")