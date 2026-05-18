from fastapi import APIRouter, Depends

from app.models.schemas import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import get_current_user, login_user, register_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# Registra un nuevo usuario (docente o alumno)
@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister):
    return register_user(data)


# Inicia sesión y devuelve un token JWT
@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    return login_user(email=data.email, password=data.password)


# Devuelve los datos del usuario autenticado
@router.get("/me", response_model=UserResponse)
def me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
