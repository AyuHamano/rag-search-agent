import pytest
import logging
from gerar_resposta.chunk_por_paragrafo import chunk_por_paragrafo

logger = logging.getLogger(__name__)

def test_chunk_agrega_paragrafos_pequenos():
    """Testa se parágrafos pequenos são unidos no mesmo chunk se couberem"""
    texto = "Primeiro parágrafo curto.\n\nSegundo parágrafo curto."
    # Limite grande o suficiente para caber os dois
    chunks = chunk_por_paragrafo(texto, chunk_size=100, overlap=0)
    
    assert len(chunks) == 1
    assert "Primeiro parágrafo curto." in chunks[0]
    assert "Segundo parágrafo curto." in chunks[0]

def test_chunk_divide_paragrafos_maiores_que_o_limite():
    """Testa se um parágrafo que ultrapassa o limite é quebrado nas sentenças"""
    texto = "Esta é a primeira frase do artigo. Esta é a segunda frase que é bem longa."
    
    # Tamanho muito restrito, vai forçar a divisão na pontuação (ponto final)
    chunks = chunk_por_paragrafo(texto, chunk_size=40, overlap=0)
    
    assert len(chunks) == 2
    assert "Esta é a primeira frase do artigo." in chunks[0]
    assert "Esta é a segunda frase que é bem longa." in chunks[1]