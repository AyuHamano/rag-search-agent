
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
from pathlib import Path



def criar_vector_store(documentos: list[dict], salvar_em: str = "db/chroma_db"):
    """
    Gera embeddings com sentence-transformers e indexa no FAISS.
    Usa modelo multilíngue leve que funciona bem em português.

    O índice é salvo em disco para não precisar reprocessar toda vez.
    """

    print("[INFO] Carregando modelo de embeddings...")
    modelo = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    textos = [doc["texto"] for doc in documentos]
    metadados = [doc["metadados"] for doc in documentos]

    print(f"[INFO] Gerando embeddings para {len(textos)} chunks...")

    embeddings = modelo.encode(textos, batch_size=32, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype="float32")

    faiss.normalize_L2(embeddings)

    dimensao = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimensao)
    index.add(embeddings)

    Path(salvar_em).mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, f"{salvar_em}/index.faiss")
    with open(f"{salvar_em}/metadados.pkl", "wb") as f:
        pickle.dump({"textos": textos, "metadados": metadados}, f)

    print(f"[INFO] Vector store salvo em '{salvar_em}/'")
    return index, textos, metadados


def carregar_vector_store(pasta: str = "db/chroma_db"):
    print( """Carrega índice FAISS e metadados salvos em disco.""")
    index = faiss.read_index(f"{pasta}/index.faiss")
    with open(f"{pasta}/metadados.pkl", "rb") as f:
        dados = pickle.load(f)

    print(f"[INFO] Vector store carregado: {index.ntotal} chunks indexados")
    return index, dados["textos"], dados["metadados"]
