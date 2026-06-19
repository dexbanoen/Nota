from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.course_repository import CourseRepository
from app.models.course import Course


class CourseService:
    """Business logic for course management."""

    def __init__(self, db: Session) -> None:
        self.repo = CourseRepository(db)

    def create_course(self, name: str) -> Course:
        name = name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Course name cannot be blank.")
        return self.repo.create_course(name)

    def get_courses(self) -> list[Course]:
        return self.repo.get_courses()

    def get_course(self, course_id: int) -> Course:
        course = self.repo.get_course_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")
        return course
