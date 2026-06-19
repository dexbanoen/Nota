from sqlalchemy.orm import Session

from app.models.course import Course


class CourseRepository:
    """Handles all database operations for Course entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_course(self, name: str) -> Course:
        course = Course(name=name)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def get_courses(self) -> list[Course]:
        return self.db.query(Course).order_by(Course.created_at.desc()).all()

    def get_course_by_id(self, course_id: int) -> Course | None:
        return self.db.query(Course).filter(Course.id == course_id).first()
