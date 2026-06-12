from app.core.db import get_connection


# Guarda la respuesta evaluada de un alumno (primer intento)
def save_student_answer(class_id, student_id, question_id, answer, correct, feedback, score, created_at, attempts=1):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO student_answers
                (class_id, student_id, question_id, answer, correct, feedback, score, created_at, attempts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (class_id, student_id, question_id, answer, correct, feedback, score, created_at, attempts)
        )
        conn.commit()
    finally:
        conn.close()


# Actualiza la respuesta de un alumno tras un reintento (portón de dominio)
def update_student_answer(class_id, student_id, question_id, answer, correct, feedback, score, attempts):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE student_answers
            SET answer = %s, correct = %s, feedback = %s, score = %s, attempts = %s
            WHERE class_id = %s AND student_id = %s AND question_id = %s
            """,
            (answer, correct, feedback, score, attempts, class_id, student_id, question_id)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve las respuestas de un alumno en una clase
def get_answers_by_student(class_id, student_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM student_answers
            WHERE class_id = %s AND student_id = %s
            ORDER BY created_at ASC
            """,
            (class_id, student_id)
        )
        return cursor.fetchall()
    finally:
        conn.close()
