"""
Servicio encargado del manejo de archivos subidos por el usuario.

Se utiliza para:
- crear carpetas necesarias
- guardar archivos temporalmente
- devolver la ruta del archivo guardado
"""

import os

from app.core.config import DATA_DIR

# Carpeta donde se guardan los archivos subidos
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


# Guarda un archivo subido dentro de la carpeta uploads
async def save_uploaded_file(
    file,
    session_id,
    content: bytes
):
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    file_path = os.path.join(
        UPLOADS_DIR,
        f"{session_id}_{file.filename}"
    )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path