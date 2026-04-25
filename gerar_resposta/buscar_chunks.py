from typing import Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient


def buscar_chunks(
    pergunta: str,
    client: QdrantClient,
    collection_name: str,
    top_k: int = 5,
    filtro_assunto: Optional[str] = None,
) -> list[dict]:
    modelo = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    query_emb = modelo.encode(pergunta, normalize_embeddings=True)

    buscar_n = top_k * 5 if filtro_assunto else top_k

    # ✅ Use query_points (qdrant-client >= 1.7) instead of search_points
    response = client.query_points(
        collection_name=collection_name,
        query=query_emb.tolist(),
        limit=buscar_n,
        with_payload=True,
    )

    resultados = []
    for hit in response.points:
        payload = hit.payload

        if (
            filtro_assunto
            and filtro_assunto.lower()
            not in payload.get("metadados", {}).get("assunto", "").lower()
        ):
            continue

        resultados.append(
            {
                "texto": payload.get("texto", ""),
                "metadados": payload.get("metadados", {}),
                "score": hit.score,
            }
        )

        if len(resultados) >= top_k:
            break

    return resultados