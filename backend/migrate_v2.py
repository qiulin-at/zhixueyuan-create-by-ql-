"""二期幂等迁移：只创建缺失的表，不重建、不写入业务数据。

用法：
    cd backend && ../.venv/Scripts/python.exe migrate_v2.py
    DATABASE_URL=mysql+pymysql://... python migrate_v2.py
"""

from sqlalchemy import inspect

from app import models  # noqa: F401  确保模型注册到 Base.metadata
from app.config import settings
from app.database import Base, engine


def main() -> None:
    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    after = set(inspect(engine).get_table_names())
    added = sorted(after - before)
    print(f"database={settings.database_url}")
    print(f"tables_before={len(before)} tables_after={len(after)}")
    print(f"added={','.join(added) if added else 'none'}")


if __name__ == "__main__":
    main()