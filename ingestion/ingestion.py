from pathlib import Path

from ingestion.carregar_metadados import carregar_metadados
from const import METADATA_FILES
from ingestion.criar_documentos import criar_documentos
from ingestion.criar_vetor_store import criar_vector_store, carregar_vector_store


def rodar_ingestion(pdf_dir: str = "./pdfs"):

    registros = carregar_metadados(METADATA_FILES)
    documentos = criar_documentos(registros, Path(pdf_dir))

    index, textos, metadados = criar_vector_store(documentos)
    index, textos, metadados = carregar_vector_store()

    return index, textos, metadados


if __name__ == "__main__":

    rodar_ingestion()
