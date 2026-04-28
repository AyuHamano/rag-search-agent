import sys
import argparse
import logging
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from .carregar_metadado import carregar_metadados
from .criar_documento import criar_documentos
from .criar_vetor_store import criar_vector_store
from .download_pdf import baixar_todos_pdfs

logger = logging.getLogger(__name__)

METADATA_FILES = [
    # str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2016_metadados-curto.json"),
    str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2016_metadados.json"),
    str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2021_metadados.json"),
    str(_PROJECT_ROOT / "dataset" / "biblioteca_aneel_gov_br_legislacao_2022_metadados.json"),
]

_CACHE_PATH = _PROJECT_ROOT / "documentos_cache.jsonl"


def rodar_ingestion(
    pdf_dir: Path = _PROJECT_ROOT / "pdfs",
    force_recreate: bool = False,
    baixar_pdfs: bool = False,
):
    if baixar_pdfs:
        logger.info("Iniciando download dos PDFs...")
        baixar_todos_pdfs()
        registros = carregar_metadados(METADATA_FILES)
        criar_documentos(registros, Path(pdf_dir), _CACHE_PATH)
    else:
        logger.info("Pulando download dos PDFs (use --baixar-pdfs para baixar).")

    client, collection_name = criar_vector_store(
        cache_path=_CACHE_PATH,
        force_recreate=force_recreate,
    )

    return client, collection_name


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline de ingestão: download dos PDFs, extração de texto e indexação.",
    )
    parser.add_argument(
        "--baixar-pdfs",
        action="store_true",
        help="Baixa os PDFs antes de processar (default: não baixa).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = _parse_args()
    rodar_ingestion(
        pdf_dir=args.pdf_dir,
        force_recreate=args.force_recreate,
        baixar_pdfs=args.baixar_pdfs,
    )