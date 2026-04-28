from pathlib import Path

PDF_DIR = Path("../pdfs")
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARQUIVO_PROGRESSO = _PROJECT_ROOT / "progresso.json"
DATASETS = [
    _PROJECT_ROOT / "rag-search-agent" / "dataset" / "biblioteca_aneel_gov_br_legislacao_2016_metadados.json",
    _PROJECT_ROOT / "rag-search-agent" / "dataset" / "biblioteca_aneel_gov_br_legislacao_2021_metadados.json",
    _PROJECT_ROOT / "rag-search-agent" / "dataset" / "biblioteca_aneel_gov_br_legislacao_2022_metadados.json",
]

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

ENCODE_BATCH = 32   
UPSERT_BATCH = 100
CHUNK_OVERLAP = 100
CHUNK_SIZE = 800
