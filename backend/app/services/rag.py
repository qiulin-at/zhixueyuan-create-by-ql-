import math
import re

from sqlalchemy.orm import Session

from ..models import Chapter, CourseMaterial

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
EN_RE = re.compile(r"[a-zA-Z0-9_]+")
PARAGRAPH_RE = re.compile(r"\n\s*\n|\n")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
MIN_SCORE = 0.06


def tokenize(text: str) -> list[str]:
    tokens = [word.lower() for word in EN_RE.findall(text)]
    for chunk in CJK_RE.findall(text):
        if len(chunk) == 1:
            tokens.append(chunk)
        else:
            tokens.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
    return tokens


def split_chunks(text: str) -> list[tuple[str, str]]:
    """按段落切分，长段落按 500 字滑窗，返回 (段落标签, 内容)。"""
    paragraphs = [part.strip() for part in PARAGRAPH_RE.split(text or "") if part.strip()]
    chunks: list[tuple[str, str]] = []
    index = 0
    buffer = ""
    for paragraph in paragraphs:
        if len(paragraph) > CHUNK_SIZE:
            if buffer:
                index += 1
                chunks.append((f"第 {index} 段", buffer))
                buffer = ""
            start = 0
            while start < len(paragraph):
                piece = paragraph[start : start + CHUNK_SIZE]
                index += 1
                chunks.append((f"第 {index} 段", piece))
                start += CHUNK_SIZE - CHUNK_OVERLAP
        elif len(buffer) + len(paragraph) + 1 <= CHUNK_SIZE:
            buffer = f"{buffer}\n{paragraph}".strip()
        else:
            if buffer:
                index += 1
                chunks.append((f"第 {index} 段", buffer))
            buffer = paragraph
    if buffer:
        index += 1
        chunks.append((f"第 {index} 段", buffer))
    if not chunks and text:
        chunks.append(("第 1 段", text[:CHUNK_SIZE]))
    return chunks


def _source_label(course_title: str, item: dict) -> str:
    if item.get("chapter_title"):
        return f"《{course_title}》第 {item['chapter_sort']} 章《{item['chapter_title']}》"
    return f"《{course_title}》资料《{item['title']}》{item.get('section', '')}"


def retrieve_materials(db: Session, course_id: int, query: str, top_k: int = 3) -> list[dict]:
    rows = (
        db.query(CourseMaterial, Chapter)
        .outerjoin(Chapter, CourseMaterial.chapter_id == Chapter.id)
        .filter(CourseMaterial.course_id == course_id, CourseMaterial.kind == "kb")
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
        for section, content in split_chunks(material.content):
            tokens = tokenize(f"{material.title} {material.keywords} {content}")
            documents.append((material, chapter, section, content, tokens))
            for token in set(tokens):
                document_frequency[token] = document_frequency.get(token, 0) + 1
    if not documents:
        return []

    total = len(documents)
    idf = {
        token: math.log((total + 1) / (count + 1)) + 1
        for token, count in document_frequency.items()
    }
    query_weight = math.sqrt(sum(idf.get(token, 1.0) ** 2 for token in query_tokens)) or 1.0
    scored = []
    for material, chapter, section, content, tokens in documents:
        token_counts: dict[str, int] = {}
        for token in tokens:
            if token in query_tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
        if not token_counts:
            continue
        match_weight = sum(
            idf.get(token, 1.0) * (1 + math.log(count)) for token, count in token_counts.items()
        )
        document_weight = math.sqrt(sum(idf.get(token, 1.0) ** 2 for token in set(tokens))) or 1.0
        score = match_weight / (query_weight * document_weight)
        if score < MIN_SCORE:
            continue
        scored.append(
            {
                "id": material.id,
                "material_id": material.id,
                "course_id": material.course_id,
                "title": material.title,
                "content": content,
                "snippet": content[:180],
                "section": section,
                "chapter_title": chapter.title if chapter is not None else "",
                "chapter_sort": chapter.sort if chapter is not None else 0,
                "score": round(score, 4),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)

    deduped = []
    seen = set()
    for item in scored:
        if item["material_id"] in seen:
            continue
        seen.add(item["material_id"])
        deduped.append(item)
        if len(deduped) >= top_k:
            break
    return deduped


def format_materials(materials: list[dict]) -> str:
    if not materials:
        return "（无匹配资料）"
    return "\n".join(
        f"- {item['chapter_title'] or item['title']} {item.get('section', '')}：{item['content']}"
        for item in materials
    )


def format_reference_line(course_title: str, materials: list[dict]) -> str:
    labels = []
    for item in materials:
        label = _source_label(course_title, item)
        if label not in labels:
            labels.append(label)
    return "参考：" + "；".join(labels) if labels else ""