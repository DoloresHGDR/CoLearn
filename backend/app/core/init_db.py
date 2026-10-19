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

        # Tabla de notificaciones para el docente (alumno se unió o salió de una clase)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                teacher_id TEXT NOT NULL,
                class_id TEXT NOT NULL,
                class_name TEXT NOT NULL,
                student_name TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('join', 'leave')),
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (class_id) REFERENCES classes(id)
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
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES class_questions(id)
            )
        """)

        # Tabla de feedback del alumno sobre la utilidad del tutor (un voto por alumno y clase)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_feedback (
                id SERIAL PRIMARY KEY,
                class_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                helpful BOOLEAN NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE(class_id, student_id)
            )
        """)

        # Migraciones idempotentes para bases de datos ya creadas.
        # Cada uno agrega una columna solo si todavía no existe (Postgres).
        migrations = [
            "ALTER TABLE classes ADD COLUMN reflection TEXT DEFAULT ''",
            "ALTER TABLE classes ADD COLUMN introduction TEXT DEFAULT ''",
            "ALTER TABLE student_answers ADD COLUMN attempts INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE classes ADD COLUMN summary TEXT DEFAULT ''",
            "ALTER TABLE classes ADD COLUMN summary_fingerprint TEXT DEFAULT ''",
            "ALTER TABLE class_enrollments ADD COLUMN practice_index INTEGER DEFAULT NULL",
        ]
        for ddl in migrations:
            cursor.execute(f"""
                DO $$ BEGIN
                    {ddl};
                EXCEPTION WHEN duplicate_column THEN NULL;
                END $$;
            """)

        conn.commit()
    finally:
        conn.close()
