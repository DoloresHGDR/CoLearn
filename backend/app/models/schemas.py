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


class ChatResponse(BaseModel):
    """Respuesta de la IA al alumno."""
    reply: str


# --- Modelos de evaluación de respuestas ---

class AnswerRequest(BaseModel):
    """Respuesta que envía el alumno a una pregunta."""
    answer: str


class EvaluationResponse(BaseModel):
    """Resultado de evaluar la respuesta con Gemini."""
    correct: str       # 'si', 'no' o 'parcial'
    feedback: str
    score: int


# --- Modelos de métricas del docente ---

class AnswerRecord(BaseModel):
    """Un intento de respuesta del alumno con su puntaje."""
    question_id: int
    correct: str
    score: int
    created_at: str


class StudentMetrics(BaseModel):
    """Participación y progreso de un alumno en la clase."""
    student_id: str
    name: str
    email: str
    message_count: int
    answers_submitted: int
    average_score: float
    score_trend: str       # 'mejorando', 'estable', 'bajando' o 'sin datos'
    answer_history: List[AnswerRecord]
    joined_at: str


class ClassMetrics(BaseModel):
    """Métricas generales de una clase para el docente."""
    class_id: str
    class_name: str
    enrolled_count: int
    students: List[StudentMetrics]


# Representa una pregunta generada por la IA para una clase
class Question(BaseModel):
    id: int
    question: str
    difficulty: str


class StudentProgress(BaseModel):
    """Progreso propio del alumno en una clase — usado para dificultad adaptativa."""
    answers_submitted: int
    average_score: float
    recommended_level: str   # 'easy', 'medium' o 'hard' (Mastery Learning — Bloom, 1968)