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

        # Tabla de clases creadas por docentes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id TEXT PRIMARY KEY,
                teacher_id TEXT NOT NULL,
                name TEXT NOT NULL,
                join_code TEXT UNIQUE NOT NULL,
                level TEXT NOT NULL,
                focuses TEXT NOT NULL,
                file_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        """)

        # Tabla de alumnos inscritos en clases
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE(class_id, student_id)
            )
        """)

        conn.commit()
    finally:
        conn.close()