import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Modelo de OpenRouter para todas las llamadas a IA (chat, generación, evaluación)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Ruta base para archivos de datos (uploads y caché)
DATA_DIR = os.getenv("DATA_DIR", "./data")

# Cadena de conexión a PostgreSQL (la define docker-compose; este default es solo para desarrollo local)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://colearn:colearn123@localhost:5433/colearn")

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "colearn-secret-key-cambiar-en-produccion")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Validación de correo institucional en el registro.
# El dominio del correo debe empezar con el prefijo del rol y terminar con el sufijo institucional.
# Ej: docente -> nombre@docente(...).edu.ar  ·  alumno -> nombre@alumno(...).edu.ar
INSTITUTIONAL_EMAIL_SUFFIX = os.getenv("INSTITUTIONAL_EMAIL_SUFFIX", ".edu.ar")
ROLE_EMAIL_PREFIX = {"student": "alumno.", "teacher": "docente."}

if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY no está configurada en .env")