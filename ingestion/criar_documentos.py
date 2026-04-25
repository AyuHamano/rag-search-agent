from pathlib import Path
import time
import random
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

        # Adiciona delay entre requisições para evitar rate limiting
        if i > 0:
            delay = random.uniform(0.5, 1.5)  # 0.5 a 1.5 segundos
            time.sleep(delay)

        pdfs = reg.get("pdfs", [])
        if not pdfs:
            continue

        pdf_info = pdfs[0]
        nome_arquivo = pdf_info.get("url", "")
        logger.info("Processando arquivo: %s (%d/%d)", nome_arquivo, i + 1, total)

        if nome_arquivo.endswith(".html") or nome_arquivo.endswith(".htm"):
            texto = extrair_texto_html(str(nome_arquivo))
        else:
            texto = extrair_texto_pdf(str(nome_arquivo))
        if not texto:
            continue

        logger.info("Texto extraído (tamanho: %d caracteres)", len(texto))

        chunks = chunk_por_paragrafo(texto, CHUNK_SIZE, CHUNK_OVERLAP)

        # Metadados enriquecidos para cada chunk
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
