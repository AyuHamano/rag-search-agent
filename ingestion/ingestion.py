import sys
import json
from pathlib import Path
import logging

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

_DOCUMENTOS_CACHE = _PROJECT_ROOT / "documentos_cache.json"


def rodar_ingestion(pdf_dir: Path = _PROJECT_ROOT / "pdfs", force_recreate: bool = False):
    if _DOCUMENTOS_CACHE.exists():
        print("Carregando documentos do cache: %s", _DOCUMENTOS_CACHE)
        documentos = json.loads(_DOCUMENTOS_CACHE.read_text(encoding="utf-8"))
    else:
        registros = carregar_metadados(METADATA_FILES)
        documentos = criar_documentos(registros, Path(pdf_dir))
        if documentos:
            _DOCUMENTOS_CACHE.write_text(
                json.dumps(documentos, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info("Cache L1 salvo: %d documentos", len(documentos))

    client, collection_name = criar_vector_store(documentos, force_recreate=force_recreate)
    return client, collection_name


if __name__ == "__main__":

    rodar_ingestion()
