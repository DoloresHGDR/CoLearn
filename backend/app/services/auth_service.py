"""
Servicio de autenticación: registro, login y obtención del usuario actual.
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.schemas import TokenResponse, UserRegister, UserResponse
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
)

# Esquema de seguridad Bearer para los endpoints protegidos
bearer_scheme = HTTPBearer()

VALID_ROLES = {"teacher", "student"}


def register_user(data: UserRegister) -> UserResponse:
    """Registra un nuevo usuario. Falla si el email ya existe o el rol es inválido."""

    if data.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail="El rol debe ser 'teacher' o 'student'."
        )

    # Verificar que el email no esté en uso
    if get_user_by_email(data.email):
        raise HTTPException(
            status_code=409,
            detail="Ya existe una cuenta con ese email."
        )

    user_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    create_user(
        user_id=user_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        created_at=created_at,
    )

    return UserResponse(id=user_id, name=data.name, email=data.email, role=data.role)


def login_user(email: str, password: str) -> TokenResponse:
    """Verifica las credenciales y devuelve un token JWT."""

    user = get_user_by_email(email)

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos."
        )

    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return TokenResponse(access_token=token)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UserResponse:
    """Dependencia que extrae y valida el token del header Authorization."""

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")

    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        role=user["role"],
    )
