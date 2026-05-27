import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import DATABASE_URL


# Crea una conexión a PostgreSQL
# RealDictCursor permite acceder a las columnas por nombre (row["campo"])
def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn
