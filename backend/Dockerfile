# Imagen base de Python
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y sentence-transformers
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python primero (mejor uso de caché de Docker)
COPY requirements.txt .
# Instalar PyTorch CPU-only primero para evitar bajar librerías NVIDIA innecesarias
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar el modelo de embeddings durante el build para no descargarlo en runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# Copiar el resto del código
COPY . .

# Crear carpetas necesarias para uploads y caché
RUN mkdir -p data/uploads data/embedding_cache

# Exponer el puerto de la API
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
