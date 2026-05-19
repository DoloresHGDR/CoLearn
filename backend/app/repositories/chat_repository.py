from app.core.db import get_connection


# Guarda un mensaje en el historial de chat
def save_message(class_id, student_id, role, content, created_at):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_messages (class_id, student_id, role, content, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (class_id, student_id, role, content, created_at)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve el historial completo de un alumno en una clase
def get_history(class_id, student_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE class_id = %s AND student_id = %s
            ORDER BY created_at ASC
            """,
            (class_id, student_id)
        )
        return cursor.fetchall()
    finally:
        conn.close()


# Devuelve los últimos N mensajes (para armar el contexto de la IA)
def get_recent_history(class_id, student_id, limit=10):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE class_id = %s AND student_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (class_id, student_id, limit)
        )
        rows = cursor.fetchall()
        return list(reversed(rows))
    finally:
        conn.close()
