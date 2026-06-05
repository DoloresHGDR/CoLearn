import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Ruta base para archivos de datos (uploads y caché)
DATA_DIR = os.getenv("DATA_DIR", "./data")

# Ruta de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "colearn.db")

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "colearn-secret-key-cambiar-en-produccion")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY no está configurada en .env")