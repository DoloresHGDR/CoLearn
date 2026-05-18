from app.core.db import get_connection


# Inicializa las tablas necesarias del sistema
def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Tabla de usuarios (docentes y alumnos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
                created_at TEXT NOT NULL
            )
        """)

        # Tabla de sesiones educativas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                level TEXT,
                focus TEXT,
                score INTEGER
            )
        """)

        # Tabla de respuestas del alumno
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question_id INTEGER,
                answer TEXT,
                feedback TEXT,
                points INTEGER
            )
        """)

        conn.commit()
    finally:
        conn.close()