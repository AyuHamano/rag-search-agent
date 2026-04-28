import pdfplumber
import pymupdf
from pathlib import Path
from io import BytesIO
import logging

from ingestion.serializar_tabela import serializar_tabela

logger = logging.getLogger(__name__)


def extrair_texto_pdf(caminho_pdf: str) -> str:
   
    if not (caminho_pdf.endswith(".pdf") or caminho_pdf.endswith(".html") or caminho_pdf.endswith(".htm")):
        logger.error("Arquivo não é PDF ou HTML: %s", caminho_pdf)
        return ""

    caminho = Path(caminho_pdf)

    try:
        pdf_bytes = caminho.read_bytes()
        print("[INFO] Lido localmente: %s", caminho.name)
        logger.info("Lido localmente: %s", caminho.name)
    except Exception as e:
        logger.error("Falha ao ler %s: %s", caminho_pdf, type(e).__name__)
        return ""

    tem_tabelas = False
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                if page.extract_tables():
                    tem_tabelas = True
                    break
    except Exception as e:
        logger.warning("Erro ao verificar tabelas em %s: %s", caminho_pdf, type(e).__name__)
        tem_tabelas = False 

    if tem_tabelas:
        logger.info("Tem tabelas - usando pdfplumber para %s", caminho_pdf)
        texto_completo = []
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    texto_pagina = page.extract_text() or ""

                    tabelas_serializadas = []
                    for tabela in page.extract_tables():
                        t = serializar_tabela(tabela)
                        if t:
                            tabelas_serializadas.append(t)

                    texto_completo.append(texto_pagina)
                    if tabelas_serializadas:
                        texto_completo.append(
                            "[TABELA]\n" + "\n".join(tabelas_serializadas)
                        )

            resultado = "\n".join(texto_completo).strip()
            logger.info("Extraído com pdfplumber (%d caracteres)", len(resultado))
            return resultado
        except Exception as e:
            logger.error("Falha ao extrair com pdfplumber: %s", type(e).__name__)
            return ""
    else:
        logger.info("Sem tabelas - usando PyMuPDF para %s", caminho_pdf)
        try:
            doc = pymupdf.open(stream=BytesIO(pdf_bytes), filetype="pdf")
            texto_completo = []

            for page_num in range(doc.page_count):
                page = doc[page_num]
                texto = page.get_text()
                texto_completo.append(texto)

            doc.close()
            resultado = "\n".join(texto_completo).strip()
            logger.info("Extraído com PyMuPDF (%d caracteres)", len(resultado))
            return resultado
        except Exception as e:
            logger.error("Falha ao extrair com PyMuPDF: %s", type(e).__name__)
            return ""
