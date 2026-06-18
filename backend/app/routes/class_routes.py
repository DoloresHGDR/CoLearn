import os
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ClassMetrics,
    ClassResponse,
    ClassSummaryResponse,
    CreateClassResponse,
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
from app.repositories.class_repository import delete_class, leave_class
from app.repositories.notification_repository import (
    count_unread,
    create_notification,
    get_notifications_by_teacher,
    mark_all_read,
)
from app.models.schemas import NotificationResponse, NotificationsResponse
from app.services.metrics_service import get_metrics
from app.services.summary_service import get_class_summary

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


# Descarga el archivo de la clase (alumno puede abrirlo con su app preferida)
@router.get("/{class_id}/file")
def download_class_file(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    from app.repositories.class_repository import get_class_by_id as _get
    classroom = _get(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    file_path = classroom.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="El archivo de la clase no está disponible.")
    return FileResponse(path=file_path, filename=os.path.basename(file_path))


# El docente ve todas las preguntas generadas para su clase (sin duplicados)
@router.get("/{class_id}/teacher-questions", response_model=List[Question])
def teacher_questions(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden ver las preguntas.")
    rows = get_questions_by_class(class_id)
    seen = set()
    unique = []
    for r in rows:
        if r["question"] not in seen:
            seen.add(r["question"])
            unique.append(Question(id=r["id"], question=r["question"], difficulty=r["difficulty"]))
    return unique


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


# El docente elimina su clase (cascade — se borra para todos)
@router.delete("/{class_id}", status_code=204)
def delete_class_route(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden eliminar clases.")
    from app.repositories.class_repository import get_class_by_id as _get
    classroom = _get(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if classroom["teacher_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="No tenés permiso para eliminar esta clase.")
    delete_class(class_id)


# El alumno sale de una clase (solo elimina su inscripción)
@router.delete("/{class_id}/leave", status_code=204)
def leave_class_route(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Solo los alumnos pueden salirse de una clase.")
    from app.repositories.class_repository import get_class_by_id as _get
    classroom = _get(class_id)
    # Notificar al docente que un alumno salió de su clase (antes de borrar la inscripción)
    if classroom:
        create_notification(
            teacher_id=classroom["teacher_id"],
            class_id=class_id,
            class_name=classroom["name"],
            student_name=current_user.name,
            event_type="leave",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    leave_class(class_id, current_user.id)


# El docente ve las métricas de participación de su clase
@router.get("/{class_id}/metrics", response_model=ClassMetrics)
def class_metrics(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden ver las métricas.")

    return get_metrics(class_id=class_id, teacher_id=current_user.id)


# El docente ve sus notificaciones (alumnos que se unieron o salieron de sus clases)
@router.get("/notifications", response_model=NotificationsResponse)
def get_notifications(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes tienen notificaciones.")
    rows = get_notifications_by_teacher(current_user.id)
    items = [
        NotificationResponse(
            id=r["id"],
            class_name=r["class_name"],
            student_name=r["student_name"],
            event_type=r["event_type"],
            is_read=r["is_read"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return NotificationsResponse(unread=count_unread(current_user.id), items=items)


# El docente marca todas sus notificaciones como leídas
@router.post("/notifications/read", status_code=204)
def read_notifications(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes tienen notificaciones.")
    mark_all_read(current_user.id)


# El docente ve un resumen de desempeño generado por IA (cacheado)
@router.get("/{class_id}/summary", response_model=ClassSummaryResponse)
def class_summary(
    class_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden ver el resumen.")

    return get_class_summary(class_id=class_id, teacher_id=current_user.id)
