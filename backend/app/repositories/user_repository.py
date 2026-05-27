from app.core.db import get_connection


# Inserta un nuevo usuario en la base de datos
def create_user(user_id, name, email, password_hash, role, created_at):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, name, email, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, name, email, password_hash, role, created_at)
        )
        conn.commit()
    finally:
        conn.close()


# Busca un usuario por email
def get_user_by_email(email):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        conn.close()


# Busca un usuario por su ID
def get_user_by_id(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()
