from pathlib import Path

from ingestion.carregar_metadados import carregar_metadados
from const import METADATA_FILES
from ingestion.criar_documentos import criar_documentos
from ingestion.criar_vetor_store import criar_vector_store, carregar_vector_store


def rodar_ingestion(pdf_dir: str = "./pdfs"):

    registros = carregar_metadados(METADATA_FILES)
    documentos = criar_documentos(registros, Path(pdf_dir))
    
    if not documentos:
        print("[Aviso] Nenhum documento original processado (provável bloqueio de rede 403). Injetando um documento de teste para a aplicação não quebrar.")
        documentos = [
            {
                "texto": "Regras de Geração Distribuída (Documento de Teste): A microgeração distribuída é caracterizada por central geradora com potência instalada menor ou igual a 75 kW. Este texto é apenas um teste pois a rede bloqueou o download dos PDFs da ANEEL.",
                "metadados": {
                    "titulo": "Documento de Teste (Mock)",
                    "url": "http://localhost",
                    "assunto": "Geração Distribuída"
                }
            }
        ]

    index, textos, metadados = criar_vector_store(documentos)
    index, textos, metadados = carregar_vector_store()

    return index, textos, metadados


if __name__ == "__main__":

    rodar_ingestion()
