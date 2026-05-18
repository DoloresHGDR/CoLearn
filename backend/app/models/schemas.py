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


# --- Modelos de sesión educativa ---

# Representa una pregunta generada por la IA
class Question(BaseModel):
    id: int
    question: str
    difficulty: str


# Respuesta enviada al crear una sesión
class CreateSessionResponse(BaseModel):
    session_id: str
    introduction: str
    questions: List[Question]
    reflection: str


# Respuesta enviada por el alumno
class StudentAnswer(BaseModel):
    session_id: str
    question_id: int
    answer: str


# Feedback generado por la IA
class FeedbackResponse(BaseModel):
    correct: bool
    feedback: str
    current_score: int


# Resultado final de la sesión
class FinalResult(BaseModel):
    total_score: int
    final_level: str
    final_reflection: str