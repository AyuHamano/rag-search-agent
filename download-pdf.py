from curl_cffi import requests as cffi_requests
from pathlib import Path
import json, time, random, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PASTA_PDFS = "./pdfs"
ARQUIVO_PROGRESSO = "./progresso.json"
DATASETS = [
    "./dataset/biblioteca_aneel_gov_br_legislacao_2016_metadados.json",
    "./dataset/biblioteca_aneel_gov_br_legislacao_2021_metadados.json",
    "./dataset/biblioteca_aneel_gov_br_legislacao_2022_metadados.json",
]

def extrair_urls(dataset_paths: list[str]) -> list[dict]:
    urls = []
    for path in dataset_paths:
        with open(path, encoding="utf-8") as f:
            dataset = json.load(f)
        for data, registros in dataset.items():
            for reg in registros["registros"]:
                for pdf in reg["pdfs"]:
                    url = pdf["url"].replace("http://", "https://")
                    urls.append({"url": url, "arquivo": pdf["arquivo"]})
    logger.info("Total de URLs extraídas: %d", len(urls))
    return urls

def carregar_progresso() -> set:
    if Path(ARQUIVO_PROGRESSO).exists():
        with open(ARQUIVO_PROGRESSO) as f:
            return set(json.load(f))
    return set()

def salvar_progresso(baixados: set):
    with open(ARQUIVO_PROGRESSO, "w") as f:
        json.dump(list(baixados), f)

def baixar_arquivo(url: str, caminho: str, max_retries: int = 3) -> bool:
    for tentativa in range(max_retries):
        try:
            response = cffi_requests.get(
                url,
                impersonate="chrome120",
                headers={
                    "Referer": "https://www2.aneel.gov.br/",
                    "Accept-Language": "pt-BR,pt;q=0.9",
                },
                timeout=30,
            )
            if response.status_code == 200:
                with open(caminho, "wb") as f:
                    f.write(response.content)
                return True
            else:
                logger.warning("Tentativa %d/%d - Status %d: %s", tentativa + 1, max_retries, response.status_code, url.split("/")[-1])
                if response.status_code in [403, 404]:
                    return False
        except Exception as e:
            logger.warning("Tentativa %d/%d - Erro: %s", tentativa + 1, max_retries, str(e)[:80])

        if tentativa < max_retries - 1:
            time.sleep((2 ** tentativa) + random.uniform(0, 1))

    return False

def baixar_todos():
    Path(PASTA_PDFS).mkdir(exist_ok=True)

    urls = extrair_urls(DATASETS)
    baixados = carregar_progresso()
    pendentes = [u for u in urls if u["arquivo"] not in baixados]

    logger.info("Total: %d | Já baixados: %d | Pendentes: %d", len(urls), len(baixados), len(pendentes))

    for i, item in enumerate(pendentes):
        url = item["url"]
        arquivo = item["arquivo"]
        caminho = f"{PASTA_PDFS}/{arquivo}"

        logger.info("[%d/%d] Baixando: %s", i + 1, len(pendentes), arquivo)

        sucesso = baixar_arquivo(url, caminho)

        if sucesso:
            baixados.add(arquivo)
        else:
            logger.error("Falhou: %s", arquivo)

        if i % 10 == 0:
            salvar_progresso(baixados)

        time.sleep(random.uniform(1, 3))

    salvar_progresso(baixados)
    logger.info("Concluído! Baixados: %d/%d", len(baixados), len(urls))

if __name__ == "__main__":
    baixar_todos()