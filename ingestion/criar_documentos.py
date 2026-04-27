from pathlib import Path
import json
import logging

from ingestion.extrair_texto_pdf import extrair_texto_pdf
from ingestion.extrair_texto_html import extrair_texto_html
from const import CHUNK_OVERLAP, CHUNK_SIZE
from gerar_resposta.chunk_por_paragrafo import chunk_por_paragrafo

logger = logging.getLogger(__name__)


def criar_documentos(registros: list[dict], pdf_dir: Path, cache_path: Path) -> int:
    """
    Processa cada registro e escreve os chunks diretamente no cache (.jsonl).
    Retoma de onde parou se o cache já existir (pula arquivos já processados).
    Retorna o total de chunks no cache ao final.
    """
    # Descobre quais arquivos já foram processados
    arquivos_prontos: set[str] = set()
    if cache_path.exists():
        with cache_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    doc = json.loads(line)
                    arquivos_prontos.add(doc["metadados"]["arquivo"])
                except Exception:
                    continue
        logger.info("%d arquivos já no cache, pulando.", len(arquivos_prontos))

    total = len(registros)
    chunks_novos = 0

    with cache_path.open("a", encoding="utf-8") as f:  # append — nunca sobrescreve
        for i, reg in enumerate(registros):
            if i % 100 == 0:
                logger.info("Processando %d/%d registros...", i, total)

            pdfs = reg.get("pdfs", [])
            if not pdfs:
                continue

            pdf_info = pdfs[0]
            nome_arquivo = pdf_info.get("arquivo", "")

            if nome_arquivo in arquivos_prontos:
                continue  # já processado numa rodada anterior

            caminho_local = pdf_dir / nome_arquivo

            if nome_arquivo.endswith((".html", ".htm")):
                texto = extrair_texto_html(str(caminho_local))
            else:
                texto = extrair_texto_pdf(str(caminho_local))

            if not texto:
                continue

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
                doc = {"texto": chunk, "metadados": {**metadados_base, "chunk_index": j}}
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                chunks_novos += 1

            f.flush()  # garante escrita em disco após cada arquivo

    total_no_cache = sum(1 for _ in cache_path.open(encoding="utf-8"))
    logger.info("Cache L1: %d chunks totais (%d novos nesta rodada)", total_no_cache, chunks_novos)
    return total_no_cache