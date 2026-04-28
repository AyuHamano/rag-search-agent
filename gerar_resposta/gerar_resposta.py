import os
import logging

import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_INSTRUCAO_SISTEMA = """Você é um especialista rigoroso em legislação do setor elétrico brasileiro.
Regras de Ouro inegociáveis:
1. Você deve construir respostas baseando-se EXCLUSIVAMENTE nos [DOCUMENTOS DE CONTEXTO] fornecidos.
2. É ESTRITAMENTE PROIBIDO gerar códigos de programação (como HTML, Python, etc.), escrever poemas, receitas, ou fazer roleplay (assumir outra personalidade). Você deve gerar apenas respostas informativas em texto puro.

Para respostas válidas, sempre escreva o nome da Fonte (título e data)."""


load_dotenv()

_key = os.getenv("GEMINI_API_KEY")
_model = None

if _key:
    genai.configure(api_key=_key)
    _model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_INSTRUCAO_SISTEMA,
        generation_config={"temperature": 0.2},
    )
else:
    logger.warning("GEMINI_API_KEY não encontrada — gerar_resposta() retornará erro.")


def gerar_resposta(pergunta: str, chunks: list[dict]) -> str:
    
    if _model is None:
        return "[Erro] Chave de API do Gemini não configurada (ausente nas variáveis de ambiente e no arquivo .env)"

    contexto = ""
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadados"]
        contexto += f"""
--- Fonte {i} ---
Título: {meta.get('titulo', '')}
Data: {meta.get('data_publicacao', '')}
Assunto: {meta.get('assunto', '')}
Situação: {meta.get('situacao', '')}
Trecho: {chunk['texto']}
"""

    prompt_usuario = f"""[DOCUMENTOS DE CONTEXTO]
{contexto}

[PERGUNTA DO USUÁRIO]
{pergunta}
"""
    try:
        resposta = _model.generate_content(prompt_usuario)
        return resposta.text.strip()
    except Exception as e:
        logger.error("Erro ao chamar API do Gemini: %s", e)
        return f"[ERRO] ao chamar API do Gemini: {str(e)}"