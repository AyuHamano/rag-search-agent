from pathlib import Path
import logging

from ingestion.extrair_texto_pdf import extrair_texto_pdf
from ingestion.extrair_texto_html import extrair_texto_html
from const import CHUNK_OVERLAP, CHUNK_SIZE
from gerar_resposta.chunk_por_paragrafo import chunk_por_paragrafo

logger = logging.getLogger(__name__)


def criar_documentos(registros: list[dict], pdf_dir: Path) -> list[dict]:
    """
    Para cada registro de metadado:
      1. Encontra o PDF correspondente
      2. Extrai o texto
      3. Divide em chunks
      4. Retorna lista de documentos com texto + metadados

    Cada documento final tem o formato:
    {
        "texto": "...",
        "metadados": {
            "titulo": "...",
            "autor": "...",
            "data_publicacao": "...",
            "assunto": "...",
            "situacao": "...",
            "arquivo": "...",
            "url": "...",
        }
    }
    """
    documentos = []
    total = len(registros)

    for i, reg in enumerate(registros):
        if i % 100 == 0:
            logger.info("Processando %d/%d registros...", i, total)

        pdfs = reg.get("pdfs", [])
        if not pdfs:
            continue

        pdf_info = pdfs[0]
        nome_arquivo = pdf_info.get("arquivo", "")
        caminho_local = pdf_dir / nome_arquivo

        logger.info("Processando arquivo: %s (%d/%d)", caminho_local, i + 1, total)

        # if not caminho_local.exists():
        #     logger.warning("Arquivo não encontrado: %s", caminho_local)
        #     continue

        if nome_arquivo.endswith(".html") or nome_arquivo.endswith(".htm"):
            texto = extrair_texto_html(str(caminho_local))
        else:
            texto = extrair_texto_pdf(str(caminho_local))
        if not texto:
            continue

        logger.info("Texto extraído (tamanho: %d caracteres)", len(texto))

        chunks = chunk_por_paragrafo(texto, CHUNK_SIZE, CHUNK_OVERLAP)

        metadados_base = {
            "titulo": reg.get("titulo", ""),
            "autor": reg.get("autor", ""),
            "data_publicacao": reg.get("data_publicacao", ""),
            "assunto": (reg.get("assunto") or "").replace("Assunto:", "").strip(),
            "situacao": (reg.get("situacao") or "").replace("Situação:", "").strip(),
            "ementa": reg.get("ementa", "") or "",
            "arquivo": nome_arquivo,
            "url": pdf_info.get("url", ""),
        }

        for j, chunk in enumerate(chunks):
            documentos.append(
                {"texto": chunk, "metadados": {**metadados_base, "chunk_index": j}}
            )

    logger.info("Total de chunks gerados: %d", len(documentos))
    return documentos
