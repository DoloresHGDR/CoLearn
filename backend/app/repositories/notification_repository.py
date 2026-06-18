from app.core.db import get_connection


# Crea una notificación para el docente (alumno se unió o salió de una clase)
def create_notification(teacher_id, class_id, class_name, student_name, event_type, created_at):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notifications (teacher_id, class_id, class_name, student_name, event_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (teacher_id, class_id, class_name, student_name, event_type, created_at)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve las notificaciones de un docente, las más nuevas primero
def get_notifications_by_teacher(teacher_id, limit=30):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE teacher_id = %s ORDER BY created_at DESC LIMIT %s",
            (teacher_id, limit)
        )
        return cursor.fetchall()
    finally:
        conn.close()


# Cuenta las notificaciones sin leer de un docente
def count_unread(teacher_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS total FROM notifications WHERE teacher_id = %s AND is_read = FALSE",
            (teacher_id,)
        )
        row = cursor.fetchone()
        return row["total"] if row else 0
    finally:
        conn.close()


# Marca todas las notificaciones de un docente como leídas
def mark_all_read(teacher_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE teacher_id = %s",
            (teacher_id,)
        )
        conn.commit()
    finally:
        conn.close()
