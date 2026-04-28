import json
import logging
from pathlib import Path
from typing import Iterator

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)
from const import EMBEDDING_MODEL, ENCODE_BATCH, UPSERT_BATCH

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_UPSERT_CHECKPOINT = _PROJECT_ROOT / "upsert_checkpoint.json"

def _enriquecer_texto(doc: dict) -> str:

    meta = doc.get("metadados", {}) or {}
    cabecalho_partes = [
        meta.get("titulo", ""),
        meta.get("assunto", ""),
        meta.get("ementa", ""),
    ]
    cabecalho = " | ".join(p for p in cabecalho_partes if p)
    if not cabecalho:
        return doc["texto"]
    return f"{cabecalho}\n\n{doc['texto']}"


def _formatar_para_e5_passage(texto: str) -> str:
   
    return f"passage: {texto}"

def _load_checkpoint_from_qdrant(
    client: QdrantClient,
    collection_name: str,
    total_ids: int,
    batch_size: int = 1000,
) -> set[int]:
    
    inserted: set[int] = set()
    for start in range(0, total_ids, batch_size):
        ids = list(range(start, min(start + batch_size, total_ids)))
        pontos = client.retrieve(
            collection_name=collection_name,
            ids=ids,
            with_payload=False,
            with_vectors=False,
        )
        inserted.update(p.id for p in pontos)

    logger.info("%d IDs confirmados direto no Qdrant.", len(inserted))
    return inserted


def _load_checkpoint(
    client: QdrantClient,
    collection_name: str,
    total_ids: int,
) -> set[int]:
    
    if _UPSERT_CHECKPOINT.exists():
        content = _UPSERT_CHECKPOINT.read_text(encoding="utf-8").strip()
        if content:
            try:
                data = json.loads(content)
                ids = set(data.get("inserted_ids", []))
                logger.info("%d IDs carregados do checkpoint JSON.", len(ids))
                return ids
            except json.JSONDecodeError:
                logger.warning("Checkpoint JSON corrompido — reconstruindo via Qdrant.")
        else:
            logger.warning("Checkpoint JSON vazio — reconstruindo via Qdrant.")

    return _load_checkpoint_from_qdrant(client, collection_name, total_ids)


def _save_checkpoint(inserted_ids: set[int]) -> None:
    _UPSERT_CHECKPOINT.write_text(
        json.dumps({"inserted_ids": sorted(inserted_ids)}, indent=2),
        encoding="utf-8",
    )

def _criar_indices_payload(client: QdrantClient, collection_name: str) -> None:
   
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="metadados.arquivo",
            field_schema=PayloadSchemaType.TEXT,
        )
        logger.info("Índice TEXT criado em 'metadados.arquivo'.")
    except Exception as e:
        logger.warning("Não foi possível criar índice em 'metadados.arquivo': %s", e)


def _iter_cache(cache_path: Path, skip_ids: set[int]) -> Iterator[tuple[int, dict]]:
   
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


def _collect_batch(
    iterator: Iterator[tuple[int, dict]], batch_size: int
) -> list[tuple[int, dict]]:
    batch = []
    for item in iterator:
        batch.append(item)
        if len(batch) >= batch_size:
            break
    return batch


def criar_vector_store(
    cache_path: Path,
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "aneel",
    force_recreate: bool = True,
) -> tuple[QdrantClient, str]:
    
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache não encontrado: {cache_path}")

    # Conta linhas do cache sem carregar tudo (necessário para o fallback do checkpoint)
    total_ids = sum(1 for _ in cache_path.open(encoding="utf-8"))
    logger.info("%d linhas no cache .jsonl.", total_ids)

    logger.info("Carregando modelo de embeddings: %s", EMBEDDING_MODEL)
    modelo = SentenceTransformer(EMBEDDING_MODEL)

    client = QdrantClient(url=qdrant_url, timeout=60)
    collections = {c.name for c in client.get_collections().collections}

    if force_recreate:
        logger.warning("force_recreate=True: apagando coleção e checkpoint.")
        if collection_name in collections:
            client.delete_collection(collection_name)
        _UPSERT_CHECKPOINT.unlink(missing_ok=True)
        collections.discard(collection_name)

    if collection_name not in collections:
        sample = modelo.encode(
            ["passage: amostra"], normalize_embeddings=True
        )
        dimensao = sample.shape[1]
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimensao, distance=Distance.COSINE),
        )
        logger.info("Coleção '%s' criada (dim=%d)", collection_name, dimensao)
        _criar_indices_payload(client, collection_name)
    else:
        logger.info("Coleção '%s' já existe — continuando de onde parou.", collection_name)
        _criar_indices_payload(client, collection_name)

    inserted_ids = _load_checkpoint(client, collection_name, total_ids)
    logger.info("%d IDs já indexados, pulando.", len(inserted_ids))

    iterator = _iter_cache(cache_path, skip_ids=inserted_ids)

    batch_num = 0
    total_inseridos = len(inserted_ids)

    while True:
        batch = _collect_batch(iterator, UPSERT_BATCH)
        if not batch:
            break

        batch_num += 1
        indices = [idx for idx, _ in batch]

        textos_para_embedar = [
            _formatar_para_e5_passage(_enriquecer_texto(doc))
            for _, doc in batch
        ]

        embeddings = modelo.encode(
            textos_para_embedar,
            batch_size=ENCODE_BATCH,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
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
            "Batch %d: IDs %d–%d inseridos | %d/%d total",
            batch_num, indices[0], indices[-1], total_inseridos, total_ids,
        )

    logger.info("Ingestão concluída: %d documentos indexados.", total_inseridos)
    return client, collection_name


def carregar_vector_store(
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "aneel",
) -> tuple[QdrantClient, str]:
    client = QdrantClient(url=qdrant_url, timeout=60)
    collections = {c.name for c in client.get_collections().collections}
    if collection_name not in collections:
        raise ValueError(f"Coleção '{collection_name}' não encontrada no Qdrant")
    info = client.get_collection(collection_name)
    logger.info("Coleção carregada: %d pontos indexados.", info.points_count)
    return client, collection_name