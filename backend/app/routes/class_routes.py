import os
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.schemas import (
    ClassResponse,
    CreateClassResponse,
    JoinClassResponse,
    UserResponse,
)
from app.services.auth_service import get_current_user
from app.services.class_service import (
    create_class_service,
    join_class_service,
    list_student_classes,
    list_teacher_classes,
)

router = APIRouter(prefix="/classes", tags=["Clases"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024


# El docente crea una nueva clase subiendo un archivo
@router.post("", response_model=CreateClassResponse, status_code=201)
async def create_class(
    name: str = Form(...),
    level: str = Form(...),
    focuses: List[str] = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden crear clases.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF, DOCX o TXT.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el límite de 20 MB.")
    await file.seek(0)

    return await create_class_service(
        teacher_id=current_user.id,
        name=name,
        level=level,
        focuses=focuses,
        file=file,
    )


# El docente ve todas sus clases
@router.get("", response_model=List[ClassResponse])
def get_my_classes(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role == "teacher":
        return list_teacher_classes(current_user.id)
    return list_student_classes(current_user.id)


# El alumno se une a una clase con el código
@router.post("/join", response_model=JoinClassResponse)
def join_class(
    join_code: str = Form(...),
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Solo los alumnos pueden unirse a clases.")

    return join_class_service(student_id=current_user.id, join_code=join_code)
