import pdfplumber
import pymupdf
import cloudscraper
import requests
from io import BytesIO
import time
import random

from ingestion.serializar_tabela import serializar_tabela

_scraper = None


def _get_scraper():
    """Retorna uma instância única de scraper para reutilizar conexões"""
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper()
    return _scraper


def extrair_texto_pdf(caminho_pdf: str, max_retries: int = 3) -> str:
    """
    Extrai todo o texto de um PDF, página por página.
    Estratégia otimizada:
    - Se NÃO tem tabelas: usa PyMuPDF (muito mais rápido)
    - Se tem tabelas: usa pdfplumber para serializar corretamente

    Com retry automático com backoff exponencial.
    """
    if caminho_pdf.startswith("http://www2.aneel.gov.br/"):
        caminho_pdf = caminho_pdf.replace("http://", "https://")
        print(f"[INFO] URL normalizada: {caminho_pdf}")

    if not (caminho_pdf.endswith(".pdf") or caminho_pdf.endswith(".html")):
        print(f"[ERRO] URL não é PDF ou HTML: {caminho_pdf}")
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer": "https://www2.aneel.gov.br/",
        "Connection": "keep-alive",
    }

    pdf_bytes = None
    for tentativa in range(max_retries):
        try:
            scraper = _get_scraper()
            response = scraper.get(caminho_pdf, headers=headers, timeout=30)
            response.raise_for_status()
            pdf_bytes = response.content
            print(f"[OK] Baixado com sucesso: {caminho_pdf.split('/')[-1]}")
            break
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            print(
                f"[AVISO] Tentativa {tentativa + 1}/{max_retries} - HTTP {status_code}: {caminho_pdf.split('/')[-1]}"
            )

            if status_code == 429:  # Rate limited
                wait_time = (2**tentativa) + random.uniform(0, 1)
                print(f"[INFO] Rate limited! Aguardando {wait_time:.1f}s...")
                time.sleep(wait_time)
            elif status_code in [403, 404]:  # Forbidden/Not found
                print(f"[ERRO] Acesso negado (HTTP {status_code}): {caminho_pdf}")
                return ""
            elif tentativa < max_retries - 1:
                wait_time = (2**tentativa) + random.uniform(0, 1)
                print(
                    f"[INFO] Aguardando {wait_time:.1f}s antes da próxima tentativa..."
                )
                time.sleep(wait_time)
            else:
                print(f"[ERRO] Falha após {max_retries} tentativas: {caminho_pdf}")
                return ""
        except Exception as e:
            print(
                f"[AVISO] Tentativa {tentativa + 1}/{max_retries} falhou: {type(e).__name__}: {str(e)[:80]}"
            )
            if tentativa < max_retries - 1:
                wait_time = (2**tentativa) + random.uniform(0, 1)
                print(f"[INFO] Aguardando {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"[ERRO] Falha ao baixar {caminho_pdf}: {type(e).__name__}")
                return ""

    if not pdf_bytes:
        return ""

    tem_tabelas = False
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                if page.extract_tables():
                    tem_tabelas = True
                    break
    except Exception as e:
        print(f"[AVISO] erro ao verificar tabelas em {caminho_pdf}: {type(e).__name__}")
        tem_tabelas = False 

    if tem_tabelas:
        print(f"[INFO] tem tabelas - usando pdfplumber para {caminho_pdf}")
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
            print(f"[INFO] extraído com pdfplumber ({len(resultado)} caracteres)")
            return resultado
        except Exception as e:
            print(f"[ERRO] falha ao extrair com pdfplumber: {type(e).__name__}")
            return ""
    else:
        print(f"[INFO] sem tabelas - usando PyMuPDF para {caminho_pdf}")
        try:
            doc = pymupdf.open(stream=BytesIO(pdf_bytes), filetype="pdf")
            texto_completo = []

            for page_num in range(doc.page_count):
                page = doc[page_num]
                texto = page.get_text()
                texto_completo.append(texto)

            doc.close()
            resultado = "\n".join(texto_completo).strip()
            print(f"[INFO] extraído com PyMuPDF ({len(resultado)} caracteres)")
            return resultado
        except Exception as e:
            print(f"[ERRO] Falha ao extrair com PyMuPDF: {type(e).__name__}")
            return ""


if __name__ == "__main__":
    caminho_pdf = "https://www2.aneel.gov.br/cedoc/prt2022588mme.pdf"  # Substitua pelo caminho do seu PDF
    texto = extrair_texto_pdf(caminho_pdf)
    print(texto)
