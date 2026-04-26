from bs4 import BeautifulSoup
import cloudscraper
import requests
import time
import random
import logging

logger = logging.getLogger(__name__)

# Session global para reutilizar conexões
_scraper = None


def _get_scraper():
    """Retorna uma instância única de scraper para reutilizar conexões"""
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper()
    return _scraper


def extrair_texto_html(url_html: str, max_retries: int = 3) -> str:
    """
    Extrai texto limpo de um arquivo HTML.
    Remove scripts, styles, e normaliza espaços em branco.
    Com retry automático com backoff exponencial.
    """
    if url_html.startswith("http://www2.aneel.gov.br/"):
        url_html = url_html.replace("http://", "https://")
        logger.info("URL normalizada: %s", url_html)

    if not url_html.endswith(".html"):
        logger.error("URL não é HTML: %s", url_html)
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer": "https://www2.aneel.gov.br/",
        "Connection": "keep-alive",
    }

    html_content = None
    for tentativa in range(max_retries):
        try:
            scraper = _get_scraper()
            response = scraper.get(url_html, headers=headers, timeout=30)
            response.raise_for_status()
            html_content = response.content
            logger.info("Baixado com sucesso: %s", url_html.split('/')[-1])
            break
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.warning("Tentativa %d/%d - HTTP %d: %s", tentativa + 1, max_retries, status_code, url_html.split('/')[-1])

            if status_code == 429:  # Rate limited
                wait_time = (2**tentativa) + random.uniform(0, 1)
                logger.info("Rate limited! Aguardando %.1fs...", wait_time)
                time.sleep(wait_time)
            elif status_code in [403, 404]:  # Forbidden/Not found
                logger.error("Acesso negado (HTTP %d): %s", status_code, url_html)
                return ""
            elif tentativa < max_retries - 1:
                wait_time = (2**tentativa) + random.uniform(0, 1)
                logger.info("Aguardando %.1fs antes da próxima tentativa...", wait_time)
                time.sleep(wait_time)
            else:
                logger.error("Falha após %d tentativas: %s", max_retries, url_html)
                return ""
        except Exception as e:
            logger.warning("Tentativa %d/%d falhou: %s: %s", tentativa + 1, max_retries, type(e).__name__, str(e)[:80])
            if tentativa < max_retries - 1:
                wait_time = (2**tentativa) + random.uniform(0, 1)
                logger.info("Aguardando %.1fs...", wait_time)
                time.sleep(wait_time)
            else:
                logger.error("Falha ao baixar %s: %s", url_html, type(e).__name__)
                return ""

    if not html_content:
        return ""

    try:
        # Parse HTML e remove scripts/styles
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script e style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Normaliza espaços em branco
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        resultado = text.strip()
        logger.info("Extraído HTML (%d caracteres)", len(resultado))
        return resultado
    except Exception as e:
        logger.error("Falha ao extrair HTML: %s", type(e).__name__)
        return ""


if __name__ == "__main__":
    url_html = "https://www2.aneel.gov.br/cedoc/ren2015698.html"  # Example
    texto = extrair_texto_html(url_html)
    print(texto[:500])  # Print first 500 chars
