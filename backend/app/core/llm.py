"""
Llamada centralizada a OpenRouter para todas las funciones de IA
(chat, generación de actividades, evaluación y resúmenes).
El modelo se configura en config.py (OPENROUTER_MODEL).
"""

import requests
from fastapi import HTTPException

from app.core.config import OPENROUTER_API_KEY, OPENROUTER_MODEL


def call_openrouter(prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
    """Envía un prompt a OpenRouter y devuelve el texto generado."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY no está configurada.")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=502, detail=f"Error de OpenRouter: {data['error']['message']}")
    if not data.get("choices"):
        raise HTTPException(status_code=502, detail="OpenRouter no devolvió ninguna respuesta válida.")
    return data["choices"][0]["message"]["content"].strip()
