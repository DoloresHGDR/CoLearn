import hashlib
import os
import pickle

import faiss

from app.core.config import DATA_DIR

# Carpeta donde se guardan los embeddings procesados
CACHE_DIR = os.path.join(DATA_DIR, "embedding_cache")


# Genera un hash único del archivo para reutilizar embeddings
def generate_file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def _get_cache_path(file_hash: str) -> str:
    return os.path.join(CACHE_DIR, f"{file_hash}.pkl")


# Guarda embeddings y datos procesados en disco
def save_cache(file_hash: str, data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _get_cache_path(file_hash)

    # Serializar el índice FAISS a bytes (pickle no lo soporta bien)
    data_to_save = {
        **data,
        "index": faiss.serialize_index(data["index"])
    }

    with open(path, "wb") as f:
        pickle.dump(data_to_save, f)


# Carga embeddings previamente procesados desde disco
def load_cache(file_hash: str):
    path = _get_cache_path(file_hash)
    if not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        data = pickle.load(f)

    # Reconstruir el índice FAISS desde bytes
    data["index"] = faiss.deserialize_index(data["index"])
    return data