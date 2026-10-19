# CoLearn

Plataforma educativa con inteligencia artificial orientada a la comprensión lectora. Permite a docentes subir materiales de estudio y generar actividades automáticamente, mientras los alumnos interactúan con una IA tutora que los guía sin darles las respuestas directamente.

Proyecto final de carrera — Ingeniería en Software, Universidad de Mendoza.

---

## ¿Qué hace?

- El **docente** sube un documento (PDF, DOCX o TXT), elige el nivel y hasta tres enfoques pedagógicos (por ejemplo, inferencia o idea principal), y el sistema genera una actividad con introducción, cinco preguntas de comprensión lectora (2 fáciles, 2 medias y 1 difícil, según la taxonomía revisada de Bloom) y una reflexión final.
- El **alumno** se une a la clase con un código corto (ej: `abc123`) y resuelve la actividad en un chat guiado con una IA tutora que trabaja solo sobre el texto del docente.
- El tutor clasifica la intención de cada mensaje (respuesta, pedido de ayuda o fuera de tema), corrige las respuestas con un segundo intento ante el error y da pistas que remiten al texto sin revelar la respuesta.
- El docente ve el desempeño de cada alumno por nivel de dificultad y un resumen escrito por la IA. Los nombres de los alumnos nunca se envían al modelo externo.

---

## Stack tecnológico

**Backend**
- Python 3.11 + FastAPI
- PostgreSQL + psycopg2
- JWT (python-jose + passlib/bcrypt)
- RAG: SentenceTransformers (`paraphrase-multilingual-mpnet-base-v2`, multilingüe) + FAISS
- OpenRouter (`openai/gpt-4o-mini`, configurable con `OPENROUTER_MODEL`) para generar actividades, evaluar respuestas, dar pistas y resumir la clase

**Frontend**
- Expo / React Native (Android)

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

### Con Docker

```bash
docker compose up -d --build
```

Levanta PostgreSQL (puerto 5433) y la API (puerto 8800). El código se copia dentro de la imagen, así que después de cada cambio hay que volver a construirla con `--build`.

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL |
| `SECRET_KEY` | Clave para firmar tokens JWT |
| `OPENROUTER_API_KEY` | Clave de OpenRouter |
| `OPENROUTER_MODEL` | Modelo de lenguaje (por defecto `openai/gpt-4o-mini`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del token en minutos (por defecto 60) |
| `DATA_DIR` | Carpeta para uploads y caché de embeddings |
| `INSTITUTIONAL_EMAIL_SUFFIX` | Sufijo del correo institucional exigido en el registro (por defecto `.edu.ar`) |

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
| GET | `/classes/{id}/file` | Alumno descarga el texto de la clase |
| POST | `/classes/{id}/chat` | Alumno envía un mensaje al tutor |
| GET | `/classes/{id}/chat` | Historial de chat del alumno |
| GET | `/classes/{id}/progress` | Avance del alumno en la actividad |
| POST | `/classes/{id}/feedback` | Alumno vota si la ayuda del tutor le resultó clara |
| GET | `/classes/{id}/teacher-questions` | Docente ve las preguntas generadas |
| GET | `/classes/{id}/metrics` | Docente ve el desempeño de cada alumno |
| GET | `/classes/{id}/summary` | Docente ve el resumen de la clase escrito por la IA |
| DELETE | `/classes/{id}` | Docente elimina la clase |
| DELETE | `/classes/{id}/leave` | Alumno abandona la clase |
| GET | `/classes/notifications` | Notificaciones del docente |
| POST | `/classes/notifications/read` | Marca las notificaciones como leídas |

---

## Tests

```bash
cd backend
pytest tests/ -v
```

Son 53 pruebas unitarias (la base de datos y la IA se reemplazan por dobles de prueba):
- `test_auth.py`: hashing de contraseñas y tokens JWT
- `test_context_loss.py`: armado del historial de la conversación
- `test_parser.py`: lectura de la actividad generada (5 preguntas: 2 fáciles, 2 medias y 1 difícil)
- `test_rag_hallucination.py`: el umbral de similitud deja el contexto vacío ante una pregunta ajena al texto
- `test_metrics.py`: métricas por alumno y nivel recomendado
- `test_summary.py`: caché del resumen del docente y que ningún nombre de alumno llegue a la IA

Los scripts `eval_umbral.py` y `eval_evaluacion.py` reproducen las mediciones del capítulo de resultados de la tesis (el segundo hace llamadas reales a OpenRouter).

---

## Estado del proyecto

| Módulo | Estado |
|---|---|
| Autenticación | ✅ Completo |
| Sistema de clases | ✅ Completo |
| Pipeline RAG | ✅ Completo |
| Chat con IA (tutor guiado) | ✅ Completo |
| Evaluación de respuestas con OpenRouter | ✅ Completo |
| Métricas y resumen del docente | ✅ Completo |
| Tests | ✅ Completo |
| Frontend mobile (Android) | ✅ Completo |

---

## Autora

**Dolores Herrera García Da Rosa**  
Ingeniería en Software — Universidad de Mendoza  
