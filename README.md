# CoLearn

Plataforma educativa con inteligencia artificial orientada a la comprensión lectora. Permite a docentes subir materiales de estudio y generar actividades automáticamente, mientras los alumnos interactúan con una IA tutora que los guía sin darles las respuestas directamente.

Proyecto final de carrera — Ingeniería en Software, Universidad de Mendoza.

---

## ¿Qué hace?

- El **docente** sube un documento (PDF, DOCX o TXT), elige el nivel y los enfoques pedagógicos, y el sistema genera una actividad completa con introducción, preguntas de dificultad progresiva y reflexión final.
- El **alumno** se une a la clase con un código corto (ej: `abc-123`) y puede chatear con una IA tutora que responde únicamente desde el texto del docente.
- El alumno puede responder las preguntas generadas y recibir feedback evaluado por Gemini.
- El docente puede ver métricas de participación: cuántos mensajes envió cada alumno, cuántas preguntas respondió y su puntaje promedio.

---

## Stack tecnológico

**Backend**
- Python 3.11 + FastAPI
- PostgreSQL + psycopg2
- JWT (python-jose + passlib/bcrypt)
- RAG: SentenceTransformers (`all-mpnet-base-v2`) + FAISS
- OpenRouter (GPT-3.5-turbo) para generación de actividades y chat
- Google Gemini (`gemini-1.5-flash`) para evaluación de respuestas

**Frontend** *(en desarrollo)*
- Expo / React Native

**Infraestructura**
- Docker + docker-compose
- Metodología 12-Factor App

---

## Arquitectura

```
frontend (Expo)
      │
      ▼
  FastAPI (REST API)
      │
      ├── routes/         ← definición de endpoints
      ├── services/       ← lógica de negocio
      ├── repositories/   ← acceso a base de datos
      ├── rag/            ← pipeline de lectura, chunking, embeddings y búsqueda
      └── core/           ← configuración, auth, caché
      │
      ▼
  PostgreSQL
```

El pipeline RAG procesa el documento del docente: lo divide en fragmentos, genera embeddings semánticos con SentenceTransformers, los indexa en FAISS y recupera los fragmentos más relevantes según la pregunta del alumno antes de llamar a la IA.

---

## Cómo levantar el backend

### Requisitos
- Python 3.11+
- PostgreSQL corriendo localmente (base de datos: `colearn`)
- Variables de entorno configuradas (ver `.env.example`)

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/DoloresHGDR/CoLearn.git
cd CoLearn/backend

# Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Completar con tus claves en .env

# Levantar el servidor
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`.  
Documentación interactiva: `http://localhost:8000/docs`

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL |
| `SECRET_KEY` | Clave para firmar tokens JWT |
| `OPENROUTER_API_KEY` | Clave de OpenRouter (GPT-3.5) |
| `GOOGLE_API_KEY` | Clave de Google Gemini |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del token en minutos |
| `DATA_DIR` | Carpeta para uploads y caché de embeddings |

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/register` | Registro de usuario |
| POST | `/auth/login` | Login, devuelve token JWT |
| GET | `/auth/me` | Datos del usuario autenticado |
| POST | `/classes` | Docente crea una clase con archivo |
| GET | `/classes` | Listar clases (del docente o del alumno) |
| POST | `/classes/join` | Alumno se une con código |
| POST | `/classes/{id}/chat` | Alumno envía mensaje a la IA |
| GET | `/classes/{id}/chat` | Historial de chat |
| GET | `/classes/{id}/questions` | Preguntas generadas de la clase |
| POST | `/classes/{id}/questions/{qid}/answer` | Alumno responde una pregunta |
| GET | `/classes/{id}/metrics` | Docente ve métricas de participación |

---

## Tests

```bash
cd backend
pytest tests/ -v
```

Incluye:
- Tests unitarios de autenticación (hashing y tokens JWT)
- Tests unitarios del parser de respuestas de la IA
- Tests de alucinación del pipeline RAG (verifica que el sistema no recupera contexto inventado)

---

## Estado del proyecto

| Módulo | Estado |
|---|---|
| Autenticación | ✅ Completo |
| Sistema de clases | ✅ Completo |
| Pipeline RAG | ✅ Completo |
| Chat con IA | ✅ Completo |
| Evaluación con Gemini | ✅ Completo |
| Métricas del docente | ✅ Completo |
| Tests | ✅ Completo |
| Frontend mobile | 🚧 En desarrollo |

---

## Autora

**Dolores Herrera García Da Rosa**  
Ingeniería en Software — Universidad de Mendoza  
