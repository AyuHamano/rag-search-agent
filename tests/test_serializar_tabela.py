import pytest
# Ajuste o import abaixo dependendo de onde o arquivo está na sua pasta real
from ingestion.serializar_tabela import serializar_tabela

def test_serializar_tabela_valida():
    """Testa se uma tabela normal é convertida na string correta"""
    tabela_falsa = [
        ["Nome", "Potência (MW)", "Estado"],  # Cabeçalhos
        ["Itaipu", "14000", "PR"],            # Linha 1
        ["Belo Monte", "11233", "PA"]         # Linha 2
    ]
    
    resultado = serializar_tabela(tabela_falsa)
    
    # Verificamos se as strings esperadas estão no resultado
    assert "Nome: Itaipu | Potência (MW): 14000 | Estado: PR" in resultado
    assert "Nome: Belo Monte | Potência (MW): 11233 | Estado: PA" in resultado

def test_serializar_tabela_com_valores_vazios_ou_quebras_de_linha():
    """Testa como a função lida com células vazias e \n (comum no pdfplumber)"""
    tabela_falsa = [
        ["Regra", "Descrição"],
        ["Art. 1", "Texto longo\ncom quebra"],
        ["Art. 2", None] # Célula vazia/nula
    ]
    
    resultado = serializar_tabela(tabela_falsa)
    
    # O \n deve ser substituído por espaço
    assert "Texto longo com quebra" in resultado
    # O None deve ser ignorado
    assert "None" not in resultado

def test_serializar_tabela_vazia_ou_incompleta():
    """Tabelas sem linhas de dados devem retornar string vazia"""
    assert serializar_tabela([]) == ""
    assert serializar_tabela([["Apenas", "Cabeçalho"]]) == ""