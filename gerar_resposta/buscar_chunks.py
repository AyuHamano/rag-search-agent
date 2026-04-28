import re
import logging
from typing import Optional

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText

logger = logging.getLogger(__name__)

_PREFIXOS_ARQUIVO = {
    "despacho": "dsp",
    "dsp": "dsp",
    "resolução homologatória": "reh",
    "resolucao homologatoria": "reh",
    "reh": "reh",
    "resolução autorizativa": "rea",
    "resolucao autorizativa": "rea",
    "rea": "rea",
    "resolução normativa": "ren",
    "resolucao normativa": "ren",
    "ren": "ren",
    "portaria": "prt",
    "prt": "prt",
}

# O número aceita pontos como separador de milhar no formato BR (ex.: "1.485").
_PADRAO_REFERENCIA = re.compile(
    r"\b(despacho|dsp|resolu[cç][aã]o\s+homologat[oó]ria|reh|"
    r"resolu[cç][aã]o\s+autorizativa|rea|resolu[cç][aã]o\s+normativa|ren|"
    r"portaria|prt)\b[^\d]{0,20}([\d.]{1,7})\s*/\s*(\d{4})",
    re.IGNORECASE,
)

def _detectar_referencia(pergunta: str) -> Optional[str]:
    """
    Detecta padrões como 'Despacho 2098/2022', 'DSP nº 1.485/2021',
    'Portaria 588/2022' e devolve o prefixo do arquivo no padrão da ANEEL,
    ex.: 'dsp20211485'.

    Aceita números no formato brasileiro com ponto separador de milhar.
    Retorna None se nenhum padrão for encontrado.
    """
    m = _PADRAO_REFERENCIA.search(pergunta)
    if not m:
        return None

    tipo, numero, ano = m.groups()
    prefixo = _PREFIXOS_ARQUIVO.get(tipo.lower().strip())
    if not prefixo:
        return None

    numero_limpo = numero.replace(".", "")
    if not numero_limpo.isdigit():
        return None

    return f"{prefixo}{ano}{int(numero_limpo):04d}"


def _formatar_para_e5_query(pergunta: str) -> str:
    """
    O modelo E5 foi treinado com instruções: queries de busca precisam
    do prefixo 'query: '. Sem ele, a qualidade da busca despenca.
    """
    return f"query: {pergunta}"

def buscar_chunks(
    pergunta: str,
    client: QdrantClient,
    collection_name: str,
    modelo: SentenceTransformer,  
    top_k: int = 5,
    filtro_assunto: Optional[str] = None,
) -> list[dict]:

    referencia = _detectar_referencia(pergunta)
    if referencia:
        logger.info("Referência detectada na pergunta: %s", referencia)
        pontos, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(must=[
                FieldCondition(
                    key="metadados.arquivo",
                    match=MatchText(text=referencia),
                )
            ]),
            limit=top_k * 3,
            with_payload=True,
        )

        if pontos:
            logger.info("Match exato encontrado: %d chunks de %s",
                        len(pontos), referencia)
            pontos.sort(
                key=lambda p: p.payload.get("metadados", {}).get("chunk_index", 0)
            )
            return [
                {
                    "texto": p.payload.get("texto", ""),
                    "metadados": p.payload.get("metadados", {}),
                    "score": 1.0,  
                }
                for p in pontos[:top_k]
            ]

        logger.warning("Referência %s detectada, mas sem match no banco — "
                       "caindo para busca semântica.", referencia)


    pergunta_formatada = _formatar_para_e5_query(pergunta)
    query_emb = modelo.encode(pergunta_formatada, normalize_embeddings=True)

    buscar_n = top_k * 5 if filtro_assunto else top_k

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

        resultados.append({
            "texto": payload.get("texto", ""),
            "metadados": payload.get("metadados", {}),
            "score": hit.score,
        })

        if len(resultados) >= top_k:
            break

    return resultados