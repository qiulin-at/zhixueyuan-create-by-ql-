import os

from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.database import Base, engine
from seed import main as seed_main


def seed_needed() -> bool:
    if os.getenv("SEED_ON_START", "true").strip().lower() not in {"1", "true", "yes"}:
        return False
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return True
    with engine.connect() as connection:
        return connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 0


def main() -> None:
    if seed_needed():
        print("[entrypoint] 数据库为空，执行 seed", flush=True)
        seed_main()
    else:
        print("[entrypoint] 跳过 seed（已有数据或 SEED_ON_START=false）", flush=True)
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()