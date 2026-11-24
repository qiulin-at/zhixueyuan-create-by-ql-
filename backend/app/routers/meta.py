from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models import TaxonomyTerm
from ..utils import ok

router = APIRouter(prefix="/api/meta", tags=["基础数据"])

FILTERS = {
    "tech_system": ["人工智能", "大数据", "云计算", "工业软件", "数通", "通信", "鸿蒙"],
    "tech_direction": [
        "语音识别",
        "图像识别",
        "数据分析",
        "数据可视化",
        "前沿技术",
        "互联网运营",
        "Python",
        "云原生",
        "移动应用",
    ],
    "level": [
        {"label": "初级课程", "value": "beginner"},
        {"label": "中级课程", "value": "intermediate"},
        {"label": "高级课程", "value": "advanced"},
        {"label": "专业共建合作课程", "value": "co_build"},
    ],
    "sort": [
        {"label": "综合排序", "value": "default"},
        {"label": "最新课程", "value": "latest"},
        {"label": "最多学习", "value": "study"},
        {"label": "最多评论", "value": "rating"},
    ],
    "course_type": [
        {"label": "理论课程", "value": "theory"},
        {"label": "实训课程", "value": "practice"},
        {"label": "认证课程", "value": "certification"},
    ],
    "job_category": ["技术", "产品", "设计", "运营", "市场", "人事/财务/行政", "高级管理"],
}


@router.get("/filters")
def get_filters():
    return ok(FILTERS)

@router.get("/taxonomy")
def get_taxonomy(db: Session = Depends(get_db)):
    rows = (
        db.query(TaxonomyTerm)
        .filter(TaxonomyTerm.enabled == 1)
        .order_by(TaxonomyTerm.kind.asc(), TaxonomyTerm.sort.asc(), TaxonomyTerm.id.asc())
        .all()
    )
    if not rows:
        return ok(FILTERS)
    grouped: dict[str, list] = {
        "course_type": [],
        "tech_system": [],
        "tech_direction": [],
        "level": [],
    }
    for term in rows:
        if term.kind in ("tech_system", "tech_direction"):
            grouped[term.kind].append(term.code)
        elif term.kind in ("course_type", "level"):
            grouped[term.kind].append({"label": term.name, "value": term.code})
    for kind, values in grouped.items():
        if not values:
            grouped[kind] = FILTERS.get(kind, [])
    return ok({**FILTERS, **grouped})