import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import settings
from .database import Base, engine
from .routers import admin, ai, assignments, auth, courses, jobs, meta, notifications, users
from .services.llm import llm_gateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("zhixueyun")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="面向教育平台的智能体开发样板工程：用户、课程、实习就业、AI 学习助手。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATUS_CODE_MAP = {400: 40001, 401: 40101, 403: 40301, 404: 40401, 409: 40901, 422: 40001}


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": STATUS_CODE_MAP.get(exc.status_code, 50001),
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    location = ".".join(str(item) for item in first.get("loc", []))
    message = f"参数校验失败：{location} {first.get('msg', '')}".strip()
    return JSONResponse(
        status_code=422,
        content={"code": 40001, "message": message, "data": None},
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 50001, "message": "服务器内部错误，请稍后重试", "data": None},
    )


@app.get("/api/health", tags=["系统"])
def health():
    database_status = "up"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("数据库健康检查失败")
        database_status = "down"
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "app": settings.app_name,
            "database": database_status,
            "llm_mode": llm_gateway.mode,
        },
    }


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(jobs.router)
app.include_router(ai.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(assignments.router)
app.include_router(meta.router)