from pathlib import Path

from carregar_metadados import carregar_metadados
from const import METADATA_FILES
from criar_documentos import criar_documentos


# teste para leitura e chunking de registros do json
def rodar_ingestion(pdf_dir: str = "./pdfs"):

    registros = carregar_metadados(METADATA_FILES)
    documentos = criar_documentos(registros, Path(pdf_dir))
    print("Exemplo de registro criado:")
    print(registros[0])

    print("Exemplo de documento criado:")
    print(documentos)


if __name__ == "__main__":

    rodar_ingestion()
