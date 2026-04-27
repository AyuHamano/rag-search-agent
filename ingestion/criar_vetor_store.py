# ingestion/criar_vetor_store.py

import json
import logging
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_UPSERT_CHECKPOINT = _PROJECT_ROOT / "upsert_checkpoint.json"

ENCODE_BATCH = 64    # encode() por vez — conservador pra não estourar RAM
UPSERT_BATCH = 100   # docs por chamada upsert — reduzido pra evitar OOM/timeout


def _load_checkpoint() -> set[int]:
    """Retorna o conjunto de IDs já inseridos no Qdrant."""
    if _UPSERT_CHECKPOINT.exists():
        data = json.loads(_UPSERT_CHECKPOINT.read_text(encoding="utf-8"))
        return set(data.get("inserted_ids", []))
    return set()


def _save_checkpoint(inserted_ids: set[int]) -> None:
    _UPSERT_CHECKPOINT.write_text(
        json.dumps({"inserted_ids": sorted(inserted_ids)}, indent=2),
        encoding="utf-8",
    )


def criar_vector_store(
    documentos: list[dict],
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "legislacao",
    force_recreate: bool = False,
) -> tuple[QdrantClient, str]:
    """
    Gera embeddings e indexa no Qdrant com dois níveis de proteção:
    - Checkpoint de IDs já inseridos (retoma após crash/timeout/OOM)
    - Encode + upsert dentro do mesmo loop (sem acumular tudo na RAM)

    Passe force_recreate=True apenas quando quiser reindexar do zero
    (apaga o checkpoint e recria a coleção).
    """
    logger.info("Carregando modelo de embeddings...")
    modelo = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    client = QdrantClient(url=qdrant_url, timeout=60)

    # --- garante que a coleção existe sem deletar o que já foi inserido ---
    collections = {c.name for c in client.get_collections().collections}

    if force_recreate:
        logger.warning("force_recreate=True: apagando coleção e checkpoint.")
        if collection_name in collections:
            client.delete_collection(collection_name)
        _UPSERT_CHECKPOINT.unlink(missing_ok=True)
        collections.discard(collection_name)

    if collection_name not in collections:
        sample_embedding = modelo.encode(["amostra"])
        dimensao = sample_embedding.shape[1]
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimensao, distance=Distance.COSINE),
        )
        logger.info("Coleção '%s' criada (dim=%d)", collection_name, dimensao)
    else:
        logger.info("Coleção '%s' já existe — continuando de onde parou.", collection_name)

    # --- filtra apenas os docs pendentes ---
    inserted_ids = _load_checkpoint()
    pendentes = [
        (i, doc) for i, doc in enumerate(documentos) if i not in inserted_ids
    ]
    logger.info(
        "%d docs totais | %d já inseridos | %d pendentes",
        len(documentos), len(inserted_ids), len(pendentes),
    )

    if not pendentes:
        logger.info("Nada a fazer — todos os documentos já estão indexados.")
        return client, collection_name

    # --- encode + upsert no mesmo loop: nunca acumula tudo na RAM ---
    total = len(pendentes)
    for start in range(0, total, UPSERT_BATCH):
        slice_idx = pendentes[start : start + UPSERT_BATCH]

        textos_batch = [doc["texto"] for _, doc in slice_idx]
        embeddings_batch = modelo.encode(
            textos_batch,
            batch_size=ENCODE_BATCH,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        points = [
            PointStruct(
                id=doc_id,
                vector=emb.tolist(),
                payload={"texto": doc["texto"], "metadados": doc["metadados"]},
            )
            for (doc_id, doc), emb in zip(slice_idx, embeddings_batch)
        ]

        try:
            client.upsert(collection_name=collection_name, points=points, wait=True)
        except Exception as e:
            logger.error(
                "Erro no batch %d–%d: %s — reinicie para retomar deste ponto.",
                start, start + len(slice_idx) - 1, e,
            )
            raise

        # Persiste o progresso imediatamente após upsert bem-sucedido
        inserted_ids.update(doc_id for doc_id, _ in slice_idx)
        _save_checkpoint(inserted_ids)

        logger.info(
            "Batch %d–%d inserido (%d/%d total).",
            start, start + len(slice_idx) - 1, len(inserted_ids), len(documentos),
        )

    logger.info("Ingestão concluída: %d documentos no Qdrant.", len(inserted_ids))
    return client, collection_name

def carregar_vector_store(
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "legislacao",
) -> tuple[QdrantClient, str]:
    client = QdrantClient(url=qdrant_url, timeout=60)
    collections = {c.name for c in client.get_collections().collections}
    if collection_name not in collections:
        raise ValueError(f"Coleção '{collection_name}' não encontrada no Qdrant")
    info = client.get_collection(collection_name)
    logger.info("Coleção carregada: %d pontos indexados.", info.points_count)
    return client, collection_name