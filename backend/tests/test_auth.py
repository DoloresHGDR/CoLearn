"""
Tests unitarios para el módulo de autenticación.
Verifica hashing de contraseñas y generación/validación de tokens JWT.
"""

import pytest
from app.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# --- Tests de contraseñas ---

class TestPassword:

    def test_hash_no_es_texto_plano(self):
        """El hash no debe ser igual a la contraseña original."""
        hashed = hash_password("mi_contraseña_secreta")
        assert hashed != "mi_contraseña_secreta"

    def test_verificacion_correcta(self):
        """verify_password debe devolver True con la contraseña correcta."""
        hashed = hash_password("abc123")
        assert verify_password("abc123", hashed) is True

    def test_verificacion_incorrecta(self):
        """verify_password debe devolver False con una contraseña equivocada."""
        hashed = hash_password("abc123")
        assert verify_password("contraseña_incorrecta", hashed) is False

    def test_misma_contraseña_genera_hashes_distintos(self):
        """bcrypt agrega sal aleatoria: dos hashes de la misma contraseña son distintos."""
        h1 = hash_password("igual")
        h2 = hash_password("igual")
        assert h1 != h2
        # Pero ambos deben verificar correctamente
        assert verify_password("igual", h1) is True
        assert verify_password("igual", h2) is True


# --- Tests de tokens JWT ---

class TestJWT:

    def test_token_se_puede_decodificar(self):
        """Un token creado debe poder decodificarse sin error."""
        token = create_access_token({"sub": "usuario-123", "role": "student"})
        payload = decode_access_token(token)
        assert payload["sub"] == "usuario-123"

    def test_token_contiene_rol(self):
        """El token debe incluir el rol del usuario."""
        token = create_access_token({"sub": "abc", "role": "teacher"})
        payload = decode_access_token(token)
        assert payload["role"] == "teacher"

    def test_token_invalido_devuelve_none(self):
        """Un token mal formado debe devolver None en lugar de lanzar excepción."""
        resultado = decode_access_token("esto.no.es.un.token.valido")
        assert resultado is None

    def test_token_manipulado_devuelve_none(self):
        """Un token modificado a mano no debe ser válido."""
        token = create_access_token({"sub": "usuario-real"})
        # Cambiar el último carácter del token
        token_modificado = token[:-1] + ("A" if token[-1] != "A" else "B")
        resultado = decode_access_token(token_modificado)
        assert resultado is None
