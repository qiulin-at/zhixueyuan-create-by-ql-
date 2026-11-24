from app.database import Base, SessionLocal, engine
from app.models import Chapter, Course, CourseMaterial
from seed import COURSE_MATERIALS


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    inserted = 0
    try:
        courses = {course.title: course for course in db.query(Course).all()}
        for group in COURSE_MATERIALS:
            course = courses.get(group["course"])
            if course is None:
                continue
            chapters = {
                chapter.title: chapter
                for chapter in db.query(Chapter).filter(Chapter.course_id == course.id).all()
            }
            for item in group["items"]:
                exists = (
                    db.query(CourseMaterial)
                    .filter(
                        CourseMaterial.course_id == course.id,
                        CourseMaterial.title == item["title"],
                    )
                    .first()
                )
                if exists is not None:
                    continue
                chapter = chapters.get(item["chapter"])
                db.add(
                    CourseMaterial(
                        course_id=course.id,
                        chapter_id=chapter.id if chapter is not None else None,
                        title=item["title"],
                        content=item["content"],
                        keywords=item["keywords"],
                    )
                )
                inserted += 1
        db.commit()
        print(f"课程资料补齐完成：新增 {inserted} 条")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()