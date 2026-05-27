from fastapi import APIRouter

router = APIRouter()


# Ruta principal del backend
@router.get("/")
def home():
    return {"message": "CoLearn backend funcionando correctamente"}


# Verifica que la API esté funcionando
@router.get("/health")
def health():
    return {"status": "ok"}
