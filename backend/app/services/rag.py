import math
import re

from sqlalchemy.orm import Session

from ..models import Chapter, CourseMaterial

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
EN_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokenize(text: str) -> list[str]:
    tokens = [word.lower() for word in EN_RE.findall(text)]
    for chunk in CJK_RE.findall(text):
        if len(chunk) == 1:
            tokens.append(chunk)
        else:
            tokens.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
    return tokens


def _source_label(course_title: str, item: dict) -> str:
    if item.get("chapter_title"):
        return f"《{course_title}》第 {item['chapter_sort']} 章《{item['chapter_title']}》"
    return f"《{course_title}》资料《{item['title']}》"


def retrieve_materials(db: Session, course_id: int, query: str, top_k: int = 3) -> list[dict]:
    rows = (
        db.query(CourseMaterial, Chapter)
        .outerjoin(Chapter, CourseMaterial.chapter_id == Chapter.id)
        .filter(CourseMaterial.course_id == course_id)
        .all()
    )
    if not rows:
        return []
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []
    documents = []
    document_frequency: dict[str, int] = {}
    for material, chapter in rows:
        tokens = tokenize(f"{material.title} {material.keywords} {material.content}")
        documents.append((material, chapter, tokens))
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1
    total = len(documents)
    scored = []
    for material, chapter, tokens in documents:
        frequencies: dict[str, int] = {}
        for token in tokens:
            if token in query_tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
        if not frequencies:
            continue
        score = 0.0
        for token, count in frequencies.items():
            idf = math.log((total + 1) / (document_frequency.get(token, 0) + 1)) + 1
            score += (1 + math.log(count)) * idf
        score /= math.sqrt(len(tokens) or 1)
        if score <= 0:
            continue
        scored.append(
            {
                "id": material.id,
                "course_id": material.course_id,
                "title": material.title,
                "content": material.content,
                "chapter_title": chapter.title if chapter is not None else "",
                "chapter_sort": chapter.sort if chapter is not None else 0,
                "score": round(score, 4),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def format_materials(materials: list[dict]) -> str:
    if not materials:
        return "（无匹配资料）"
    return "\n".join(
        f"- {item['chapter_title'] or item['title']}：{item['content']}" for item in materials
    )


def format_reference_line(course_title: str, materials: list[dict]) -> str:
    labels = []
    for item in materials:
        label = _source_label(course_title, item)
        if label not in labels:
            labels.append(label)
    return "参考：" + "；".join(labels) if labels else ""