import logging
import re

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Modelo utilizado para generar embeddings semánticos
model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2"
)


# Divide el texto en chunks y genera embeddings
def prepare_data(text):
    text = text.replace("\n", " ").strip()

    # Separar texto en oraciones
    sentences = re.split(r'(?<=[.!?])\s+', text)
    total_sentences = len(sentences)

    # Ajustar tamaño de chunk según longitud del texto
    if total_sentences < 10:
        chunk_size = 1
    elif total_sentences < 30:
        chunk_size = 2
    elif total_sentences < 80:
        chunk_size = 3
    else:
        chunk_size = 5

    # Crear chunks agrupando oraciones
    chunks = []
    for i in range(0, total_sentences, chunk_size):
        chunk = " ".join(sentences[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    # Generar embeddings
    embeddings = model.encode(chunks)
    embeddings = np.array(embeddings).astype("float32")

    logger.info(f"Chunking completado: {total_sentences} oraciones, {len(chunks)} chunks (tamaño {chunk_size})")

    return chunks, embeddings