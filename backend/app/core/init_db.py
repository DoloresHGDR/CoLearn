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
                id SERIAL PRIMARY KEY,
                class_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE(class_id, student_id)
            )
        """)

        # Tabla de preguntas generadas por la IA para cada clase
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_questions (
                id SERIAL PRIMARY KEY,
                class_id TEXT NOT NULL,
                question_order INTEGER NOT NULL,
                question TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            )
        """)

        # Tabla de mensajes del chat entre el alumno y la IA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                class_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        """)

        # Tabla de respuestas de alumnos a preguntas evaluadas por la IA (OpenRouter)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_answers (
                id SERIAL PRIMARY KEY,
                class_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                correct TEXT NOT NULL,
                feedback TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        """)

        conn.commit()
    finally:
        conn.close()
