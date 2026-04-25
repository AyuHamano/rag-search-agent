from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def criar_vector_store(
    documentos: list[dict],
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "legislacao",
):
    """
    Gera embeddings com sentence-transformers e indexa no Qdrant.
    Usa modelo multilíngue leve que funciona bem em português.

    Os dados são salvos no Qdrant server (com persistência em disco).
    """

    print("[INFO] Carregando modelo de embeddings...")
    modelo = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    print("[INFO] Conectando ao Qdrant...")
    client = QdrantClient(url=qdrant_url)

    textos = [doc["texto"] for doc in documentos]
    metadados = [doc["metadados"] for doc in documentos]

    print(f"[INFO] Gerando embeddings para {len(textos)} chunks...")

    embeddings = modelo.encode(textos, batch_size=32, show_progress_bar=True)
    dimensao = embeddings.shape[1]

    # Criar ou recriar coleção
    try:
        client.delete_collection(collection_name=collection_name)
        print(f"[INFO] Coleção '{collection_name}' removida (para recriar)")
    except:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dimensao, distance=Distance.COSINE),
    )
    print(f"[INFO] Coleção '{collection_name}' criada")

    # Inserir pontos no Qdrant
    points = []
    for i, (embedding, texto, metadata) in enumerate(
        zip(embeddings, textos, metadados)
    ):
        point = PointStruct(
            id=i,
            vector=embedding.tolist(),
            payload={
                "texto": texto,
                "metadados": metadata,
            },
        )
        points.append(point)

    client.upsert(
        collection_name=collection_name,
        points=points,
    )

    print(f"[INFO] {len(points)} documentos inseridos no Qdrant")
    return client, collection_name


def carregar_vector_store(
    qdrant_url: str = "http://localhost:6333", collection_name: str = "legislacao"
):
    """Conecta ao Qdrant e retorna client + nome da coleção."""
    print("[INFO] Conectando ao Qdrant...")
    client = QdrantClient(url=qdrant_url)

    # Verificar se coleção existe
    collections = client.get_collections()
    if collection_name not in [c.name for c in collections.collections]:
        raise ValueError(f"Coleção '{collection_name}' não encontrada no Qdrant")

    collection_info = client.get_collection(collection_name)
    print(f"[INFO] Coleção carregada: {collection_info.points_count} pontos indexados")
    return client, collection_name

