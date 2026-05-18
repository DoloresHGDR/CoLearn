"""
Servicio encargado de coordinar el pipeline RAG.

Se utiliza para:
- procesar archivos
- generar embeddings
- crear índices FAISS
- recuperar contexto relevante
- reutilizar cache semántico
"""

from app.core.cache import (
    generate_file_hash,
    load_cache,
    save_cache
)

from app.rag.reader import read_file

from app.rag.chunker import (
    prepare_data,
    model
)

from app.rag.indexer import (
    create_index,
    search_context
)


# Ejecuta el flujo completo de procesamiento RAG
def process_rag_pipeline(
    file_path,
    content

):

    # Generar hash del archivo para reutilizar cache
    file_hash = generate_file_hash(content)

    # Intentar cargar datos previamente procesados
    cached_data = load_cache(file_hash)

    if cached_data:
        text = cached_data["text"]
        chunks = cached_data["chunks"]
        embeddings = cached_data["embeddings"]
        index = cached_data["index"]
    else:

        # Leer y procesar archivo
        text = read_file(file_path)

        chunks, embeddings = prepare_data(text)

        # Crear índice FAISS
        index = create_index(embeddings)

        # Guardar resultados en cache
        save_cache(
            file_hash,
            {
                "text": text,
                "chunks": chunks,
                "embeddings": embeddings,
                "index": index
            }
        )

    # Recuperar contexto relevante
    context = search_context(
        question="comprensión lectora",
        chunks=chunks,
        index=index,
        model=model
    )

    return {
        "text": text,
        "chunks": chunks,
        "index": index,
        "context": context
    }