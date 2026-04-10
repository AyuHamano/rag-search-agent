
import os
import json
from pathlib import Path
from typing import Optional

import pdfplumber

from const import IGNORAR_REVOGADOS


def carregar_metadados(arquivos: list[str]) -> list[dict]:
    """
    Lê os JSONs e retorna lista plana de registros,
    já com o campo 'data_publicacao' preenchido.
    Filtra documentos revogados se configurado.
    """
    registros = []

    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            print(f"[AVISO] Arquivo não encontrado: {arquivo}")
            continue

        with open(arquivo, encoding="utf-8") as f:
            data = json.load(f)

        for data_pub, valor in data.items():
            if not isinstance(valor, dict):
                continue
            for reg in valor.get("registros", []):
                # Filtrar revogados
                situacao = reg.get("situacao", "")
                if IGNORAR_REVOGADOS and "REVOGADO" in situacao.upper():
                    continue

                reg["data_publicacao"] = data_pub
                registros.append(reg)

    print(f"[INFO] Total de registros carregados: {len(registros)}")
    return registros
