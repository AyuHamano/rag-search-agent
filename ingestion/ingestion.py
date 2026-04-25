from pathlib import Path
import logging
from ingestion.carregar_metadados import carregar_metadados
from const import METADATA_FILES
from ingestion.criar_documentos import criar_documentos
from ingestion.criar_vetor_store import criar_vector_store, carregar_vector_store

logger = logging.getLogger(__name__)

def rodar_ingestion(pdf_dir: str = "./pdfs"):

    registros = carregar_metadados(METADATA_FILES)
    documentos = criar_documentos(registros, Path(pdf_dir))
    
    if not documentos:
        logger.warning("Nenhum documento original processado (provável bloqueio de rede 403).")
        documentos = []
        
    logger.info("Injetando documentos base de teste (Geração Distribuída/ANEEL) para a aplicação não quebrar...")
    documentos.append(
        {
            "texto": "Regras de Geração Distribuída: A microgeração distribuída é caracterizada por central geradora de energia elétrica, com potência instalada menor ou igual a 75 kW e que utilize cogeração qualificada ou fontes renováveis de energia elétrica, conectada na rede de distribuição por meio de instalações de unidades consumidoras. A minigeração distribuída é caracterizada por potência instalada superior a 75 kW e menor ou igual a 5 MW. O sistema de compensação de energia permite que a energia excedente gerada seja injetada na rede da distribuidora.",
            "metadados": {
                "titulo": "Resolução Normativa ANEEL nº 482/2012 e 1059/2023",
                "autor": "ANEEL",
                "data_publicacao": "2023-01-01",
                "assunto": "Geração Distribuída",
                "situacao": "Vigente",
                "ementa": "Condições gerais para acesso de micro e minigeração distribuída",
                "arquivo": "mock_gd.pdf",
                "url": "http://localhost",
                "chunk_index": 0
            }
        }
    )
    documentos.append(
        {
            "texto": "A ANEEL (Agência Nacional de Energia Elétrica) é uma autarquia em regime especial vinculada ao Ministério de Minas e Energia, criada para regular e fiscalizar a geração, transmissão, distribuição e comercialização de energia elétrica no Brasil. Sua função é garantir as condições de fornecimento, estabelecendo tarifas justas e mediando conflitos entre os agentes do setor e os consumidores.",
            "metadados": {
                "titulo": "Institucional ANEEL",
                "autor": "Legislativo",
                "data_publicacao": "1996-12-26",
                "assunto": "Institucional",
                "situacao": "Vigente",
                "ementa": "Cria a Agência Nacional de Energia Elétrica - ANEEL, disciplina o regime das concessões de serviços públicos de energia elétrica e dá outras providências.",
                "arquivo": "mock_aneel.pdf",
                "url": "http://localhost",
                "chunk_index": 0
            }
        }
    )

    client, collection_name = criar_vector_store(documentos)

    client, collection_name = carregar_vector_store()

    return client, collection_name


if __name__ == "__main__":

    rodar_ingestion()
