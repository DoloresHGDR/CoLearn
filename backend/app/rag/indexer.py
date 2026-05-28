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


# Umbral de distancia L2 para considerar un chunk relevante.
# Con embeddings normalizados: L2=1.2 equivale a similitud coseno ≈ 0.28.
# Por encima de este umbral, el contenido se considera fuera de tema.
SIMILARITY_THRESHOLD = 1.2


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

    # Buscar similitud en FAISS
    distances, indices = index.search(question_embedding, k)

    # Filtrar chunks que superen el umbral de similitud
    context = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(chunks) and dist <= SIMILARITY_THRESHOLD:
            context.append(chunks[idx])

    logger.info(
        f"Contexto recuperado: {len(context)} chunks relevantes de {total_chunks} disponibles "
        f"(umbral L2={SIMILARITY_THRESHOLD})"
    )
    return "\n".join(context)