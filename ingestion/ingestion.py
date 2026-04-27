# ingestion/pipeline.py

import sys
import logging
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ingestion.carregar_metadados import carregar_metadados
from ingestion.criar_documentos import criar_documentos
from ingestion.criar_vetor_store import criar_vector_store, carregar_vector_store

logger = logging.getLogger(__name__)

METADATA_FILES = [
    # str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2016_metadados-curto.json"),
    str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2016_metadados.json"),
    str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2021_metadados.json"),
    str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2022_metadados.json"),
]

_CACHE_PATH = _PROJECT_ROOT / "documentos_cache.jsonl"


def rodar_ingestion(pdf_dir: Path = _PROJECT_ROOT / "pdfs", force_recreate: bool = False):
    # L1: extrai PDFs e salva chunks no .jsonl (retoma se já existir)
    registros = carregar_metadados(METADATA_FILES)
    criar_documentos(registros, Path(pdf_dir), _CACHE_PATH)

    # L2: lê o .jsonl em streaming e indexa no Qdrant (retoma via checkpoint)
    client, collection_name = criar_vector_store(
        cache_path=_CACHE_PATH,
        force_recreate=force_recreate,
    )

    return client, collection_name


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    rodar_ingestion()