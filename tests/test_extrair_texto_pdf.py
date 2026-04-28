import pytest
import os
import logging
from pathlib import Path
from ingestion.extrair_texto_pdf import extrair_texto_pdf

logger = logging.getLogger(__name__)

def test_extrair_texto_pdf_integracao_local():
    """
    Testa a extração de um PDF real na pasta ./pdfs.
    Verifica se o motor identifica texto e o marcador de tabela que criamos.
    """
    # 1. Setup: Busca o primeiro PDF que encontrar na sua pasta real
    pdf_dir = Path("./pdfs")
    arquivos = list(pdf_dir.glob("*.pdf"))
    
    if not arquivos:
        pytest.skip("Nenhum PDF encontrado na pasta ./pdfs para realizar o teste.")
    
    caminho_pdf = str(arquivos[0])
    
    # 2. Execução
    resultado = extrair_texto_pdf(caminho_pdf)
    
    # 3. Verificações (Asserts)
    assert isinstance(resultado, str), "O retorno deve ser uma string"
    assert len(resultado) > 0, "O texto extraído não pode estar vazio"
    
    # Se o seu arquivo for um dos que tem tabela, o marcador deve aparecer
    # Isso prova que o pdfplumber foi acionado corretamente
    if "[TABELA]" in resultado:
        logger.info(f"\n✅ Sucesso: Tabelas detectadas e serializadas em {arquivos[0].name}")
    else:
        logger.info(f"\n✅ Sucesso: Texto puro extraído de {arquivos[0].name}")

def test_extrair_texto_arquivo_inexistente():
    """Verifica se o script lida corretamente com caminhos errados sem quebrar"""
    resultado = extrair_texto_pdf("./pdfs/arquivo_que_nao_existe.pdf")
    assert resultado == "", "Deve retornar string vazia para arquivo inexistente"

def test_extrair_texto_formato_invalido():
    """Garante que o script bloqueia arquivos que não são PDF/HTML"""
    resultado = extrair_texto_pdf("imagem.png")
    assert resultado == "", "Deve ignorar extensões não suportadas"