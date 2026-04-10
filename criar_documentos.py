
import os
import json
import re
from pathlib import Path
from typing import Optional

from extrair_texto_pdf import extrair_texto_pdf
from const import PDF_DIR, CHUNK_OVERLAP, CHUNK_SIZE
from chunk_por_paragrafo import chunk_por_paragrafo


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
            print(f"[INFO] Processando {i}/{total} registros...")

        pdfs = reg.get("pdfs", [])
        if not pdfs:
            continue

        # Usar o primeiro PDF (Texto Integral)
        pdf_info = pdfs[0]
        nome_arquivo = pdf_info.get("url", "")
        print(f"[INFO] Processando PDF: {nome_arquivo} ({i+1}/{total})")
        caminho_pdf = pdf_dir / nome_arquivo


        # if not caminho_pdf.exists():
        #     continue 
        
        texto = extrair_texto_pdf(str(nome_arquivo))
        if not texto:
            continue

        print(f"[INFO] Texto extraído (tamanho: {len(texto)} caracteres)")
        
        
        
        
        chunks = chunk_por_paragrafo(texto, CHUNK_SIZE, CHUNK_OVERLAP)

        # Metadados enriquecidos para cada chunk
        metadados_base = {
            "titulo": reg.get("titulo", ""),
            "autor": reg.get("autor", ""),
            "data_publicacao": reg.get("data_publicacao", ""),
            "assunto": reg.get("assunto", "").replace("Assunto:", "").strip(),
            "situacao": reg.get("situacao", "").replace("Situação:", "").strip(),
            "ementa": reg.get("ementa", "") or "",
            "arquivo": nome_arquivo,
            "url": pdf_info.get("url", ""),
        }

        for j, chunk in enumerate(chunks):
            documentos.append({
                "texto": chunk,
                "metadados": {**metadados_base, "chunk_index": j}
            })

    print(f"[INFO] Total de chunks gerados: {len(documentos)}")
    return documentos
