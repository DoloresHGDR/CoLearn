from app.core.db import get_connection


# Devuelve una huella de las respuestas de la clase para saber si cambiaron
# (cantidad de respuestas + suma de puntajes — cambia con respuestas nuevas o reintentos)
def get_class_answer_stats(class_id: str) -> dict:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS total, COALESCE(SUM(score), 0) AS sum_scores
            FROM student_answers
            WHERE class_id = %s
            """,
            (class_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()


# Devuelve el puntaje promedio y cantidad de respuestas del propio alumno
def get_my_stats(class_id: str, student_id: str) -> dict:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*)                  AS answers_submitted,
                COALESCE(AVG(score), 0)   AS average_score
            FROM student_answers
            WHERE class_id = %s AND student_id = %s
            """,
            (class_id, student_id)
        )
        return cursor.fetchone()
    finally:
        conn.close()


# Devuelve el historial de respuestas de un alumno con la dificultad de cada pregunta
def get_student_answer_history(class_id: str, student_id: str) -> list:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sa.question_id, sa.correct, sa.score, sa.created_at,
                   COALESCE(cq.difficulty, 'desconocido') AS difficulty
            FROM student_answers sa
            LEFT JOIN class_questions cq ON sa.question_id = cq.id
            WHERE sa.class_id = %s AND sa.student_id = %s
            ORDER BY sa.created_at ASC
            """,
            (class_id, student_id)
        )
        return cursor.fetchall()
    finally:
        conn.close()


# Devuelve los datos de participación de los alumnos en una clase
def get_class_metrics(class_id: str) -> list:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Alumnos inscriptos con su cantidad de mensajes y puntaje promedio
        cursor.execute(
            """
            SELECT
                u.id            AS student_id,
                u.name          AS name,
                u.email         AS email,
                e.joined_at     AS joined_at,
                COUNT(DISTINCT m.id)    AS message_count,
                COUNT(DISTINCT a.id)    AS answers_submitted,
                COALESCE(AVG(a.score), 0) AS average_score
            FROM class_enrollments e
            JOIN users u ON u.id = e.student_id
            LEFT JOIN chat_messages m
                ON m.student_id = e.student_id
                AND m.class_id = e.class_id
                AND m.role = 'user'
            LEFT JOIN student_answers a
                ON a.student_id = e.student_id
                AND a.class_id = e.class_id
            WHERE e.class_id = %s
            GROUP BY u.id, u.name, u.email, e.joined_at
            ORDER BY e.joined_at ASC
            """,
            (class_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()
