"""二期幂等迁移：建缺失表、补缺失列、初始化分类字典，不重建、不写业务数据。

用法：
    cd backend && ../.venv/Scripts/python.exe migrate_v2.py
    DATABASE_URL=mysql+pymysql://... python migrate_v2.py
"""

from sqlalchemy import inspect, text

from app import models  # noqa: F401  确保模型注册到 Base.metadata
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import TaxonomyTerm
from app.routers.meta import FILTERS
from app.utils import ok  # noqa: F401  保持模块导入顺序


def _literal(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return None


def add_missing_columns() -> list[str]:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    added: list[str] = []
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in columns:
                    continue
                ddl = (
                    f"ALTER TABLE {table.name} ADD COLUMN {column.name} "
                    f"{column.type.compile(dialect=engine.dialect)}"
                )
                if column.default is not None and getattr(column.default, "is_scalar", False):
                    literal = _literal(column.default.arg)
                    if literal is not None:
                        ddl += f" DEFAULT {literal}"
                connection.execute(text(ddl))
                added.append(f"{table.name}.{column.name}")
    return added


def seed_taxonomy() -> int:
    db = SessionLocal()
    try:
        if db.query(TaxonomyTerm).count() > 0:
            return 0
        rows = []
        for kind in ("course_type", "level"):
            for index, item in enumerate(FILTERS[kind]):
                rows.append(
                    TaxonomyTerm(kind=kind, code=item["value"], name=item["label"], sort=index)
                )
        for kind in ("tech_system", "tech_direction"):
            for index, name in enumerate(FILTERS[kind]):
                rows.append(TaxonomyTerm(kind=kind, code=name, name=name, sort=index))
        db.add_all(rows)
        db.commit()
        return len(rows)
    finally:
        db.close()


def main() -> None:
    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    after = set(inspect(engine).get_table_names())
    tables_added = sorted(after - before)
    columns_added = add_missing_columns()
    taxonomy_added = seed_taxonomy()
    print(f"database={settings.database_url}")
    print(f"tables_before={len(before)} tables_after={len(after)}")
    print(f"tables_added={','.join(tables_added) if tables_added else 'none'}")
    print(f"columns_added={','.join(columns_added) if columns_added else 'none'}")
    print(f"taxonomy_added={taxonomy_added}")


if __name__ == "__main__":
    main()