import os
from typing import List

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form
)

from app.services.session_service import (
    create_session_service
)

from app.models.schemas import (
    CreateSessionResponse
)

router = APIRouter()

# Tipos de archivo permitidos
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Tamaño máximo: 20 MB
MAX_FILE_SIZE = 20 * 1024 * 1024


# Ruta principal del backend
@router.get("/")
def home():
    return {
        "message": "CoLearn backend funcionando correctamente"
    }


# Verifica que la API esté funcionando
@router.get("/health")
def health():
    return {
        "status": "ok"
    }


# Crea una nueva sesión educativa
@router.post(
    "/session/create",
    response_model=CreateSessionResponse
)
async def create_session(
    file: UploadFile = File(...),
    level: str = Form(...),
    focuses: List[str] = Form(...)
):
    # Validar extensión del archivo
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF, DOCX o TXT."
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el límite de 20 MB."
        )

    # Reiniciar puntero para que el servicio pueda leer el archivo
    await file.seek(0)

    return await create_session_service(
        file=file,
        level=level,
        focuses=focuses
    )