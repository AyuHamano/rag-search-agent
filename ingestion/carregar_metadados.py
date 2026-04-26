import os
import json
import logging

from const import IGNORAR_REVOGADOS

logger = logging.getLogger(__name__)

def carregar_metadados(arquivos: list[str]) -> list[dict]:
    """
    Lê os JSONs e retorna lista plana de registros,
    já com o campo 'data_publicacao' preenchido.
    Filtra documentos revogados se configurado.
    """
    registros = []

    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            logger.warning("Arquivo não encontrado: %s", arquivo)
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

    logger.info("Total de registros carregados: %d", len(registros))
    return registros
