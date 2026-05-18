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

    # Generar embedding de la pregunta
    question_embedding = np.array(
        model.encode([question])
    ).astype("float32")

    # Buscar similitud en FAISS
    distances, indices = index.search(question_embedding, k)

    # Recuperar chunks encontrados
    context = []
    for i in indices[0]:
        if i < len(chunks):
            context.append(chunks[i])

    logger.info(f"Contexto recuperado: {len(context)} chunks de {total_chunks} disponibles")
    return "\n".join(context)