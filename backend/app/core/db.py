import sqlite3

from app.core.config import DATABASE_URL


# Crea una conexión a la base de datos SQLite
def get_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn