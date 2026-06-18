from app.core.db import get_connection


# Inserta una nueva clase en la base de datos
def create_class(class_id, teacher_id, name, join_code, level, focuses, file_path, introduction, reflection, created_at):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO classes (id, teacher_id, name, join_code, level, focuses, file_path, introduction, reflection, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (class_id, teacher_id, name, join_code, level, ",".join(focuses), file_path, introduction, reflection, created_at)
        )
        conn.commit()
    finally:
        conn.close()


# Busca una clase por su código de unión
def get_class_by_code(join_code):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE join_code = %s", (join_code,))
        return cursor.fetchone()
    finally:
        conn.close()


# Busca una clase por su ID
def get_class_by_id(class_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE id = %s", (class_id,))
        return cursor.fetchone()
    finally:
        conn.close()


# Guarda el resumen de desempeño generado por IA junto con la huella de los datos
def update_class_summary(class_id, summary, fingerprint):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE classes SET summary = %s, summary_fingerprint = %s WHERE id = %s",
            (summary, fingerprint, class_id)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve todas las clases de un docente
def get_classes_by_teacher(teacher_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM classes WHERE teacher_id = %s ORDER BY created_at DESC",
            (teacher_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


# Inscribe a un alumno en una clase
def enroll_student(class_id, student_id, joined_at):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO class_enrollments (class_id, student_id, joined_at)
            VALUES (%s, %s, %s)
            """,
            (class_id, student_id, joined_at)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve el índice de práctica del alumno (None si no está practicando)
def get_practice_index(class_id, student_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT practice_index FROM class_enrollments WHERE class_id = %s AND student_id = %s",
            (class_id, student_id)
        )
        row = cursor.fetchone()
        return row["practice_index"] if row else None
    finally:
        conn.close()


# Setea el índice de práctica (None para terminar la práctica)
def set_practice_index(class_id, student_id, index):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE class_enrollments SET practice_index = %s WHERE class_id = %s AND student_id = %s",
            (index, class_id, student_id)
        )
        conn.commit()
    finally:
        conn.close()


# Verifica si un alumno ya está inscrito en una clase
def is_enrolled(class_id, student_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM class_enrollments WHERE class_id = %s AND student_id = %s",
            (class_id, student_id)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


# Elimina una clase y todo su contenido (CASCADE)
def delete_class(class_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for table in ["student_answers", "chat_messages", "class_questions", "class_enrollments", "notifications"]:
            cursor.execute(f"DELETE FROM {table} WHERE class_id = %s", (class_id,))
        cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        conn.commit()
    finally:
        conn.close()


# Elimina la inscripción de un alumno y todo su progreso en esa clase (sin borrar la clase)
def leave_class(class_id, student_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Borrar el progreso del alumno: respuestas e historial de chat de esta clase
        cursor.execute(
            "DELETE FROM student_answers WHERE class_id = %s AND student_id = %s",
            (class_id, student_id)
        )
        cursor.execute(
            "DELETE FROM chat_messages WHERE class_id = %s AND student_id = %s",
            (class_id, student_id)
        )
        cursor.execute(
            "DELETE FROM class_enrollments WHERE class_id = %s AND student_id = %s",
            (class_id, student_id)
        )
        conn.commit()
    finally:
        conn.close()


# Devuelve todas las clases en las que está inscrito un alumno
def get_classes_by_student(student_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.* FROM classes c
            JOIN class_enrollments e ON c.id = e.class_id
            WHERE e.student_id = %s
            ORDER BY e.joined_at DESC
            """,
            (student_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()
