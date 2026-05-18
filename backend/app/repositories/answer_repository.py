from app.core.db import get_connection


# Guarda la respuesta del alumno en la base de datos
def save_answer(
    session_id,
    question_id,
    answer,
    feedback,
    points
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO answers (
                session_id,
                question_id,
                answer,
                feedback,
                points
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, question_id, answer, feedback, points)
        )
        conn.commit()
    finally:
        conn.close()