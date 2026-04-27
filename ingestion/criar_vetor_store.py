# ingestion/criar_vetor_store.py

import json
import logging
from pathlib import Path
from typing import Iterator

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_UPSERT_CHECKPOINT = _PROJECT_ROOT / "upsert_checkpoint.json"

ENCODE_BATCH = 64   
UPSERT_BATCH = 100  


def _load_checkpoint() -> set[int]:
    """Retorna o conjunto de IDs (linha do .jsonl) já inseridos no Qdrant."""
    if _UPSERT_CHECKPOINT.exists():
        data = json.loads(_UPSERT_CHECKPOINT.read_text(encoding="utf-8"))
        return set(data.get("inserted_ids", []))
    return set()


def _save_checkpoint(inserted_ids: set[int]) -> None:
    _UPSERT_CHECKPOINT.write_text(
        json.dumps({"inserted_ids": sorted(inserted_ids)}, indent=2),
        encoding="utf-8",
    )


def _iter_cache(cache_path: Path, skip_ids: set[int]) -> Iterator[tuple[int, dict]]:
    """
    Lê o .jsonl linha a linha (sem carregar tudo na RAM).
    Yield: (linha_index, documento)
    Pula automaticamente os IDs já inseridos no checkpoint.
    """
    with cache_path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i in skip_ids:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Linha %d inválida no cache, pulando.", i)
                continue


def _collect_batch(
    iterator: Iterator[tuple[int, dict]], batch_size: int
) -> list[tuple[int, dict]]:
    """Coleta até batch_size itens do iterador."""
    batch = []
    for item in iterator:
        batch.append(item)
        if len(batch) >= batch_size:
            break
    return batch


def criar_vector_store(
    cache_path: Path,
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "legislacao",
    force_recreate: bool = False,
) -> tuple[QdrantClient, str]:
    """
    Indexa documentos no Qdrant lendo o cache .jsonl em streaming.

    - Nunca carrega tudo na RAM: lê UPSERT_BATCH linhas por vez
    - Retoma de onde parou via checkpoint de IDs
    - Passe force_recreate=True para reindexar do zero
    """
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache não encontrado: {cache_path}")

    logger.info("Carregando modelo de embeddings...")
    modelo = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    client = QdrantClient(url=qdrant_url, timeout=60)
    collections = {c.name for c in client.get_collections().collections}

    if force_recreate:
        logger.warning("force_recreate=True: apagando coleção e checkpoint.")
        if collection_name in collections:
            client.delete_collection(collection_name)
        _UPSERT_CHECKPOINT.unlink(missing_ok=True)
        collections.discard(collection_name)

    if collection_name not in collections:
        sample = modelo.encode(["amostra"])
        dimensao = sample.shape[1]
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimensao, distance=Distance.COSINE),
        )
        logger.info("Coleção '%s' criada (dim=%d)", collection_name, dimensao)
    else:
        logger.info("Coleção '%s' já existe — continuando de onde parou.", collection_name)

    inserted_ids = _load_checkpoint()
    logger.info("%d IDs já no checkpoint, pulando.", len(inserted_ids))

    iterator = _iter_cache(cache_path, skip_ids=inserted_ids)

    batch_num = 0
    total_inseridos = len(inserted_ids)

    while True:
        batch = _collect_batch(iterator, UPSERT_BATCH)
        if not batch:
            break

        batch_num += 1
        indices = [idx for idx, _ in batch]
        textos = [doc["texto"] for _, doc in batch]

        embeddings = modelo.encode(
            textos,
            batch_size=ENCODE_BATCH,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        points = [
            PointStruct(
                id=idx,
                vector=emb.tolist(),
                payload={"texto": doc["texto"], "metadados": doc["metadados"]},
            )
            for (idx, doc), emb in zip(batch, embeddings)
        ]

        try:
            client.upsert(collection_name=collection_name, points=points, wait=True)
        except Exception as e:
            logger.error(
                "Timeout/erro no batch %d (IDs %d–%d): %s — reinicie para retomar.",
                batch_num, indices[0], indices[-1], e,
            )
            raise

        inserted_ids.update(indices)
        _save_checkpoint(inserted_ids)
        total_inseridos += len(batch)

        logger.info(
            "Batch %d: IDs %d–%d inseridos | %d no total",
            batch_num, indices[0], indices[-1], total_inseridos,
        )

    logger.info("Ingestão concluída: %d documentos indexados.", total_inseridos)
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