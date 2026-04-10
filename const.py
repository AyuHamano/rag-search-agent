from pathlib import Path

# Diretórios
PDF_DIR = Path("./pdfs")

# Arquivos de metadados JSON
METADATA_FILES = [
    "./dados_grupo_estudos/biblioteca_aneel_gov_br_legislacao_2016_metadados-curto.json",
    # "./dados_grupo_estudos/biblioteca_aneel_gov_br_legislacao_2021_metadados.json",
    # "./dados_grupo_estudos/biblioteca_aneel_gov_br_legislacao_2022_metadados.json",
]

CHUNK_SIZE = 800     
CHUNK_OVERLAP = 150     

IGNORAR_REVOGADOS = False