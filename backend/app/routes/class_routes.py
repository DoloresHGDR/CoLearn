import os
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.schemas import (
    AnswerRequest,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ClassMetrics,
    ClassResponse,
    CreateClassResponse,
    EvaluationResponse,
    JoinClassResponse,
    UserResponse,
)
from app.models.schemas import Question
from app.repositories.question_repository import get_questions_by_class
from app.services.auth_service import get_current_user
from app.services.chat_service import get_chat_history, send_message
from app.services.class_service import (
    create_class_service,
    join_class_service,
    list_student_classes,
    list_teacher_classes,
)
from app.services.evaluation_service import evaluate_student_answer
from app.services.metrics_service import get_metrics

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


# El alumno envía un mensaje y recibe la respuesta de la IA
@router.post("/{class_id}/chat", response_model=ChatResponse)
def chat(
    class_id: str,
    body: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Solo los alumnos pueden chatear en una clase.")

    return send_message(
        class_id=class_id,
        student_id=current_user.id,
        message=body.message,
    )


# El alumno ve su historial de chat en una clase
@router.get("/{class_id}/chat", response_model=List[ChatMessage])
def chat_history(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Solo los alumnos tienen historial de chat.")

    return get_chat_history(class_id=class_id, student_id=current_user.id)


# Devuelve las preguntas generadas para una clase
@router.get("/{class_id}/questions", response_model=List[Question])
def get_questions(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    rows = get_questions_by_class(class_id)
    return [
        Question(id=r["id"], question=r["question"], difficulty=r["difficulty"])
        for r in rows
    ]


# El alumno responde una pregunta y recibe evaluación de Gemini
@router.post("/{class_id}/questions/{question_id}/answer", response_model=EvaluationResponse)
def answer_question(
    class_id: str,
    question_id: int,
    body: AnswerRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Solo los alumnos pueden responder preguntas.")

    return evaluate_student_answer(
        class_id=class_id,
        student_id=current_user.id,
        question_id=question_id,
        answer=body.answer,
    )


# El docente ve las métricas de participación de su clase
@router.get("/{class_id}/metrics", response_model=ClassMetrics)
def class_metrics(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden ver las métricas.")

    return get_metrics(class_id=class_id, teacher_id=current_user.id)
