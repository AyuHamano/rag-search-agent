from typing import Optional
from sentence_transformers import SentenceTransformer


def buscar_chunks(
    pergunta: str,
    index,
    textos: list[str],
    metadados: list[dict],
    top_k: int = 5,
    filtro_assunto: Optional[str] = None,
) -> list[dict]:
    """
    Busca os chunks mais relevantes para a pergunta.
    Suporta filtro por assunto (metadado) antes do ranking semântico.

    Retorna lista de dicts com texto + metadados + score.
    """

    modelo = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    query_emb = modelo.encode([pergunta], normalize_embeddings=True).astype("float32")

    # Buscar mais candidatos se houver filtro (para compensar os que serão removidos)
    buscar_n = top_k * 5 if filtro_assunto else top_k
    scores, indices = index.search(query_emb, buscar_n)

    resultados = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx == -1:
            continue
        meta = metadados[idx]

        # Filtro opcional por assunto
        if (
            filtro_assunto
            and filtro_assunto.lower() not in meta.get("assunto", "").lower()
        ):
            continue

        resultados.append(
            {
                "texto": textos[idx],
                "metadados": meta,
                "score": float(score),
            }
        )

        if len(resultados) >= top_k:
            break

    return resultados
