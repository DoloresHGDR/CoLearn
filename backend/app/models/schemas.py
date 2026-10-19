from typing import List

from pydantic import BaseModel, EmailStr


# --- Modelos de autenticación ---

class UserRegister(BaseModel):
    """Datos para registrar un nuevo usuario."""
    name: str
    email: EmailStr
    password: str
    role: str  # 'teacher' o 'student'


class UserLogin(BaseModel):
    """Datos para iniciar sesión."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token JWT devuelto al hacer login."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Datos del usuario que se devuelven al cliente (sin contraseña)."""
    id: str
    name: str
    email: str
    role: str


# --- Modelos de clases ---

class ClassResponse(BaseModel):
    """Datos de una clase devueltos al cliente."""
    id: str
    name: str
    join_code: str
    level: str
    focuses: List[str]
    created_at: str


class CreateClassResponse(BaseModel):
    """Respuesta completa al crear una clase: datos + actividad generada por la IA."""
    class_info: ClassResponse
    introduction: str
    questions: List["Question"]
    reflection: str


class JoinClassResponse(BaseModel):
    """Respuesta al unirse a una clase."""
    message: str
    class_info: ClassResponse


# --- Modelos de chat ---

class ChatMessage(BaseModel):
    """Un mensaje del historial de chat."""
    role: str       # 'user' o 'assistant'
    content: str
    created_at: str


class ChatRequest(BaseModel):
    """Mensaje que envía el alumno."""
    message: str


class FeedbackRequest(BaseModel):
    """Voto del alumno sobre si la ayuda del tutor le resultó clara/útil."""
    helpful: bool


class ChatResponse(BaseModel):
    """Respuesta de la IA al alumno."""
    reply: str


class ProgressResponse(BaseModel):
    """Avance del alumno en la actividad: preguntas cerradas sobre el total."""
    answered: int
    total: int
    current_question: str | None = None  # pregunta activa (para mostrarla fija en el chat)


# --- Modelos de métricas del docente ---

class AnswerRecord(BaseModel):
    """Un intento de respuesta del alumno con su puntaje."""
    question_id: int
    correct: str
    score: int
    difficulty: str    # 'easy', 'medium' o 'hard'
    created_at: str


class StudentMetrics(BaseModel):
    """Participación y progreso de un alumno en la clase."""
    student_id: str
    name: str
    email: str
    message_count: int
    answers_submitted: int
    average_score: float
    score_by_difficulty: dict  # {'easy': avg, 'medium': avg, 'hard': avg} — niveles sin respuesta se omiten
    answer_history: List[AnswerRecord]
    joined_at: str


class ClassMetrics(BaseModel):
    """Métricas generales de una clase para el docente."""
    class_id: str
    class_name: str
    enrolled_count: int
    students: List[StudentMetrics]
    feedback_total: int = 0      # cuántos alumnos votaron sobre la utilidad del tutor
    feedback_positive: int = 0   # cuántos de ellos la encontraron clara/útil


class ClassSummaryResponse(BaseModel):
    """Resumen de desempeño de la clase generado por IA (para el docente)."""
    summary: str
    generated: bool


# Representa una pregunta generada por la IA para una clase
class Question(BaseModel):
    id: int
    question: str
    difficulty: str


# --- Modelos de notificaciones del docente ---

class NotificationResponse(BaseModel):
    """Una notificación: un alumno se unió o salió de una clase."""
    id: int
    class_name: str
    student_name: str
    event_type: str   # 'join' o 'leave'
    is_read: bool
    created_at: str


class NotificationsResponse(BaseModel):
    """Lista de notificaciones del docente con el conteo sin leer."""
    unread: int
    items: List[NotificationResponse]