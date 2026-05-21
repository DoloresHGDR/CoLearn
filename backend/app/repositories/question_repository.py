from app.core.db import get_connection


# Guarda una pregunta generada por la IA para una clase
def save_question(class_id, order, question, difficulty):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO class_questions (class_id, question_order, question, difficulty)
            VALUES (%s, %s, %s, %s)
            """,
            (class_id, order, question, difficulty)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve todas las preguntas de una clase ordenadas
def get_questions_by_class(class_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, question_order, question, difficulty
            FROM class_questions
            WHERE class_id = %s
            ORDER BY question_order ASC
            """,
            (class_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()
