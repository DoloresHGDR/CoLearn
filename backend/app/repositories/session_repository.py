from app.core.db import get_connection


# Crea una nueva sesión en la base de datos
def create_session_db(
    session_id,
    level,
    focuses
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        focuses_text = ",".join(focuses)
        cursor.execute(
            """
            INSERT INTO sessions (
                id,
                level,
                focus,
                score
            )
            VALUES (?, ?, ?, ?)
            """,
            (session_id, level, focuses_text, 0)
        )
        conn.commit()
    finally:
        conn.close()


# Actualiza el puntaje acumulado de una sesión
def update_score(session_id, points):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE sessions
            SET score = score + ?
            WHERE id = ?
            """,
            (points, session_id)
        )
        conn.commit()
    finally:
        conn.close()


# Obtiene los datos de una sesión
def get_session(session_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM sessions
            WHERE id = ?
            """,
            (session_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()