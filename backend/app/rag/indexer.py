import logging

import faiss
import numpy as np

logger = logging.getLogger(__name__)


# Crea un índice FAISS para búsqueda semántica
def create_index(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index


# Umbral de distancia para considerar relevante un chunk.
# IndexFlatL2 devuelve la distancia L2 al cuadrado. Con embeddings
# normalizados, d² = 2 - 2·cos, así que 1.2 equivale a una
# similitud coseno de 0.40. Por encima, el chunk se descarta.
DISTANCE_THRESHOLD = 1.2


# Recupera los chunks más relevantes según la pregunta
def search_context(question, chunks, index, model):
    # Cantidad adaptativa de chunks a recuperar
    total_chunks = len(chunks)
    if total_chunks <= 5:
        k = 2
    elif total_chunks <= 15:
        k = 4
    else:
        k = 6

    # Generar embedding normalizado de la pregunta
    question_embedding = np.array(
        model.encode([question], normalize_embeddings=True)
    ).astype("float32")

    # Buscar los chunks más cercanos en FAISS
    distances, indices = index.search(question_embedding, k)

    # Conservar solo los chunks dentro del umbral, el resto se descarta
    context = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(chunks) and dist <= DISTANCE_THRESHOLD:
            context.append(chunks[idx])

    logger.info(
        f"Contexto recuperado: {len(context)} chunks relevantes de {total_chunks} disponibles "
        f"(umbral de distancia={DISTANCE_THRESHOLD})"
    )
    return "\n".join(context)