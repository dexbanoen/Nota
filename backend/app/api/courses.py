from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.course_service import CourseService
from app.schemas.course_schema import CreateCourseRequest, CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(payload: CreateCourseRequest, db: Session = Depends(get_db)):
    service = CourseService(db)
    return service.create_course(payload.name)


@router.get("", response_model=list[CourseResponse])
def list_courses(db: Session = Depends(get_db)):
    service = CourseService(db)
    return service.get_courses()


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    service = CourseService(db)
    return service.get_course(course_id)
