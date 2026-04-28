from bs4 import BeautifulSoup
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def extrair_texto_html(caminho_html: str) -> str:
   
    if not (caminho_html.endswith(".html") or caminho_html.endswith(".htm")):
        logger.error("Arquivo não é HTML: %s", caminho_html)
        return ""

    caminho = Path(caminho_html)
    if not caminho.exists():
        logger.error("Arquivo não encontrado: %s", caminho_html)
        return ""

    try:
        html_content = caminho.read_bytes()
        logger.info("Lido localmente: %s", caminho.name)
    except Exception as e:
        logger.error("Falha ao ler %s: %s", caminho_html, type(e).__name__)
        return ""

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()

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
    caminho_html = "./pdfs/2016/ren2016756.html"
    texto = extrair_texto_html(caminho_html)
    print(texto[:500])
