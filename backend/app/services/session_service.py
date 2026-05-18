"""
Servicio encargado de coordinar la creación de sesiones educativas.

Se utiliza para:
- guardar archivos
- ejecutar el pipeline RAG
- generar actividades
- almacenar memoria temporal
- devolver la respuesta final al cliente
"""

from uuid import uuid4

from app.core.database import sessions_cache

from app.repositories.session_repository import (
    create_session_db
)

from app.services.file_service import (
    save_uploaded_file
)

from app.services.rag_service import (
    process_rag_pipeline
)

from app.services.generation_service import (
    generate_activity
)

from app.services.parser_service import (
    parse_generated_activity
)

from app.models.schemas import (
    CreateSessionResponse
)


# Coordina todo el flujo de creación de sesión
async def create_session_service(
    file,
    level,
    focuses
):

    # Generar identificador único de sesión
    session_id = str(uuid4())

    # Guardar sesión en base de datos
    create_session_db(
        session_id=session_id,
        level=level,
        focuses=focuses
    )

    # Leer el contenido del archivo antes de guardarlo
    content = await file.read()

    # Guardar archivo subido
    file_path = await save_uploaded_file(
        file=file,
        session_id=session_id,
        content=content
    )

    # Ejecutar procesamiento RAG
    rag_data = process_rag_pipeline(
        file_path=file_path,
        content=content
    )

    # Generar actividad educativa
    generated_text = generate_activity(
        level=level,
        focuses=focuses,
        context=rag_data["context"]

    )

    # Convertir respuesta del modelo en datos estructurados
    parsed = parse_generated_activity(
        generated_text
    )

    # Guardar información temporal en memoria
    sessions_cache[session_id] = {
        "text": rag_data["text"],
        "chunks": rag_data["chunks"],
        "index": rag_data["index"],
        "questions": [
            q.model_dump()
            for q in parsed["questions"]
        ]
    }

    # Devolver respuesta final
    return CreateSessionResponse(
        session_id=session_id,
        introduction=parsed["introduction"],
        questions=parsed["questions"],
        reflection=parsed["reflection"]

    )