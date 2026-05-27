"""
Servicio de clases: crear, unirse y listar clases educativas.
"""

import secrets
import string
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.models.schemas import ClassResponse, CreateClassResponse, JoinClassResponse
from app.repositories.class_repository import (
    create_class,
    enroll_student,
    get_class_by_code,
    get_class_by_id,
    get_classes_by_student,
    get_classes_by_teacher,
    is_enrolled,
)
from app.repositories.question_repository import get_questions_by_class, save_question
from app.services.file_service import save_uploaded_file
from app.services.generation_service import generate_activity
from app.services.parser_service import parse_generated_activity
from app.services.rag_service import process_rag_pipeline


def _generate_join_code() -> str:
    """Genera un código corto y único tipo 'abc-123' usando aleatoriedad segura."""
    letters = "".join(secrets.choice(string.ascii_lowercase) for _ in range(3))
    numbers = "".join(secrets.choice(string.digits) for _ in range(3))
    return f"{letters}-{numbers}"


def _row_to_class_response(row) -> ClassResponse:
    """Convierte una fila de la DB en un ClassResponse."""
    return ClassResponse(
        id=row["id"],
        name=row["name"],
        join_code=row["join_code"],
        level=row["level"],
        focuses=row["focuses"].split(","),
        created_at=row["created_at"],
    )


async def create_class_service(teacher_id, name, level, focuses, file) -> CreateClassResponse:
    """Crea una nueva clase: guarda el archivo, procesa el RAG y genera la actividad."""

    class_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    # Generar código único (reintenta si ya existe)
    join_code = _generate_join_code()
    while get_class_by_code(join_code):
        join_code = _generate_join_code()

    # Leer y guardar el archivo subido
    content = await file.read()
    file_path = await save_uploaded_file(file=file, session_id=class_id, content=content)

    # Procesar el texto con el pipeline RAG
    rag_data = process_rag_pipeline(file_path=file_path, content=content)

    # Generar la actividad educativa con la IA
    generated_text = generate_activity(level=level, focuses=focuses, context=rag_data["context"])
    parsed = parse_generated_activity(generated_text)

    # Guardar la clase en la DB
    create_class(
        class_id=class_id,
        teacher_id=teacher_id,
        name=name,
        join_code=join_code,
        level=level,
        focuses=focuses,
        file_path=file_path,
        created_at=created_at,
    )

    # Guardar las preguntas generadas en la DB (no en memoria)
    for i, question in enumerate(parsed["questions"], start=1):
        save_question(
            class_id=class_id,
            order=i,
            question=question.question,
            difficulty=question.difficulty
        )

    class_info = ClassResponse(
        id=class_id,
        name=name,
        join_code=join_code,
        level=level,
        focuses=focuses,
        created_at=created_at,
    )

    return CreateClassResponse(
        class_info=class_info,
        introduction=parsed["introduction"],
        questions=parsed["questions"],
        reflection=parsed["reflection"],
    )


def list_teacher_classes(teacher_id) -> list[ClassResponse]:
    """Devuelve todas las clases creadas por un docente."""
    rows = get_classes_by_teacher(teacher_id)
    return [_row_to_class_response(r) for r in rows]


def join_class_service(student_id, join_code) -> JoinClassResponse:
    """Inscribe a un alumno en una clase usando el código."""

    classroom = get_class_by_code(join_code)
    if not classroom:
        raise HTTPException(status_code=404, detail="No existe ninguna clase con ese código.")

    if is_enrolled(classroom["id"], student_id):
        raise HTTPException(status_code=409, detail="Ya estás inscrito en esta clase.")

    joined_at = datetime.now(timezone.utc).isoformat()
    enroll_student(class_id=classroom["id"], student_id=student_id, joined_at=joined_at)

    return JoinClassResponse(
        message="Te uniste a la clase correctamente.",
        class_info=_row_to_class_response(classroom),
    )


def list_student_classes(student_id) -> list[ClassResponse]:
    """Devuelve todas las clases a las que se unió un alumno."""
    rows = get_classes_by_student(student_id)
    return [_row_to_class_response(r) for r in rows]
