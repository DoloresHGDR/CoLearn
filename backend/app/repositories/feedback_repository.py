from app.core.db import get_connection


# Guarda (o actualiza) el voto del alumno sobre la utilidad del tutor. Un voto por alumno y clase.
def save_feedback(class_id, student_id, helpful, created_at):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO class_feedback (class_id, student_id, helpful, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (class_id, student_id)
            DO UPDATE SET helpful = EXCLUDED.helpful, created_at = EXCLUDED.created_at
            """,
            (class_id, student_id, helpful, created_at)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve cuántos alumnos votaron y cuántos lo encontraron útil, para una clase
def get_feedback_stats(class_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE helpful) AS positive
            FROM class_feedback
            WHERE class_id = %s
            """,
            (class_id,)
        )
        row = cursor.fetchone()
        if not row:
            return {"total": 0, "positive": 0}
        return {"total": int(row["total"]), "positive": int(row["positive"])}
    finally:
        conn.close()
