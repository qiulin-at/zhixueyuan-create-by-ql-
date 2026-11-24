import ipaddress
import socket
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from ..models import User, UserLLMConfig
from .crypto import decrypt_secret, encrypt_secret

PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "zhipu": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "moonshot": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "custom": {"base_url": "", "model": ""},
}

ALLOWED_HOSTS = {
    "api.deepseek.com",
    "dashscope.aliyuncs.com",
    "open.bigmodel.cn",
    "api.moonshot.cn",
    "api.openai.com",
}


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:3]}****{value[-4:]}"


def _reject_private_address(host: str) -> None:
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, 443)}
    except socket.gaierror as exc:
        raise ValueError("Base URL 域名无法解析") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise ValueError("Base URL 不允许指向内网或保留地址")


def validate_config(provider: str, base_url: str, model: str) -> tuple[str, str]:
    if provider not in PROVIDERS:
        raise ValueError("不支持的厂商")
    url = (base_url or PROVIDERS[provider]["base_url"]).strip().rstrip("/")
    model_name = (model or PROVIDERS[provider]["model"]).strip()
    if not url:
        raise ValueError("请填写 Base URL")
    if not model_name:
        raise ValueError("请填写模型名称")
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Base URL 必须使用 https")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("Base URL 缺少域名")
    if host in ALLOWED_HOSTS:
        return url, model_name
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("Base URL 不允许指向内网或保留地址")
    except ValueError as exc:
        if "内网" in str(exc):
            raise
    _reject_private_address(host)
    return url, model_name


def config_public(config: UserLLMConfig) -> dict:
    key = decrypt_secret(config.api_key_cipher)
    return {
        "configured": bool(key),
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
        "masked_key": mask_key(key),
        "enabled": bool(config.enabled),
        "last_tested_at": config.last_tested_at.isoformat() if config.last_tested_at else None,
        "last_test_ok": None if config.last_test_ok is None else bool(config.last_test_ok),
    }


def resolve_user_config(db: Session, user: User) -> dict | None:
    config = (
        db.query(UserLLMConfig)
        .filter(UserLLMConfig.user_id == user.id, UserLLMConfig.enabled == 1)
        .first()
    )
    if config is None:
        return None
    key = decrypt_secret(config.api_key_cipher)
    if not key:
        return None
    return {
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
        "api_key": key,
    }


def save_config(
    db: Session,
    user: User,
    provider: str,
    base_url: str,
    model: str,
    api_key: str,
    enabled: bool,
) -> UserLLMConfig:
    url, model_name = validate_config(provider, base_url, model)
    config = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == user.id).first()
    if config is None:
        config = UserLLMConfig(user_id=user.id)
        db.add(config)
    config.provider = provider
    config.base_url = url
    config.model = model_name
    config.enabled = 1 if enabled else 0
    if api_key.strip():
        config.api_key_cipher = encrypt_secret(api_key.strip())
    db.commit()
    db.refresh(config)
    return config