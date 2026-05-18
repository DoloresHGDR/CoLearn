from fastapi import FastAPI

from app.core.init_db import init_db
from app.routes.auth_routes import router as auth_router
from app.routes.class_routes import router as class_router
from app.routes.routes import router as main_router

# Inicializar base de datos al iniciar la aplicación
init_db()

# Crear aplicación FastAPI
app = FastAPI(
    title="CoLearn API",
    version="1.0.0"
)

# Registrar rutas de la API
app.include_router(auth_router)
app.include_router(class_router)
app.include_router(main_router)