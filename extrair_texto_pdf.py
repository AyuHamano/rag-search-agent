import pdfplumber
import cloudscraper
import requests
import time
from io import BytesIO

from serializar_tabela import serializar_tabela


import pdfplumber
import pymupdf
import cloudscraper
import requests
import time
from io import BytesIO

from serializar_tabela import serializar_tabela


def extrair_texto_pdf(caminho_pdf: str, max_retries: int = 1) -> str:
    """
    Extrai todo o texto de um PDF, página por página.
    Estratégia otimizada:
    - Se NÃO tem tabelas: usa PyMuPDF (muito mais rápido)
    - Se tem tabelas: usa pdfplumber para serializar corretamente
    """
    if caminho_pdf.startswith("http://www2.aneel.gov.br/"):
        caminho_pdf = caminho_pdf.replace("http://", "https://")
        print(f"[INFO] URL normalizada: {caminho_pdf}")

    if not caminho_pdf.endswith(".pdf"):
        print(f"[ERRO] URL não é PDF: {caminho_pdf}")
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
            scraper = cloudscraper.create_scraper()
            response = scraper.get(caminho_pdf, headers=headers, timeout=30)
            response.raise_for_status()
            pdf_bytes = response.content
            break
        except Exception as e1:
            print(
                f"[AVISO] Tentativa {tentativa + 1} com cloudscraper falhou: {type(e1).__name__}"
            )

            if tentativa == max_retries - 1:
                try:
                    response = requests.get(
                        caminho_pdf, headers=headers, timeout=30, allow_redirects=True
                    )
                    response.raise_for_status()
                    pdf_bytes = response.content
                    break
                except Exception as e2:
                    print(
                        f"[ERRO] ✗ Falha ao baixar {caminho_pdf}: {type(e2).__name__}"
                    )
                    return ""
            # else:
            #     wait_time = 2**tentativa
            #     print(f"[INFO] Aguardando {wait_time}s antes da próxima tentativa...")
            #     time.sleep(wait_time)

    if not pdf_bytes:
        return ""

    # Etapa 1: Verifica RAPIDAMENTE se tem tabelas usando pdfplumber
    tem_tabelas = False
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                if page.extract_tables():
                    tem_tabelas = True
                    break
    except Exception as e:
        print(f"[AVISO] erro ao verificar tabelas em {caminho_pdf}: {type(e).__name__}")
        tem_tabelas = False  # Assume que não tem se der erro

    # Etapa 2: Extrai texto com a estratégia apropriada
    if tem_tabelas:
        # Usa pdfplumber (mais lento mas extrai tabelas corretamente)
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
        # Usa PyMuPDF (MUITO mais rápido)
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
