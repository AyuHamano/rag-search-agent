from pathlib import Path

PDF_DIR = Path("./pdfs")

METADATA_FILES = [
    # "./dataset/biblioteca_aneel_gov_br_legislacao_2021_metadados.json",
    # "./dataset/biblioteca_aneel_gov_br_legislacao_2022_metadados.json",
    "./dataset/biblioteca_aneel_gov_br_legislacao_2016_metadados-curto.json",
]

CHUNK_SIZE = 800     
CHUNK_OVERLAP = 150     

IGNORAR_REVOGADOS = False
