import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Em produção/CI-CD o .env pode não existir, pq as variáveis de ambiente são injetadas pelos Secrets do GitHub Actions
# load_dotenv() lida com isso silenciosamente.
# As variáveis de ambiente do SO terao prioridade se override=False (padrão).
load_dotenv()

def gerar_resposta(pergunta: str, chunks: list[dict], api_key: str = None) -> str:
    """
    Envia pergunta + chunks recuperados para o LLM via Google Gemini.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return "[Erro] Chave de API do Gemini não configurada (ausente nas variáveis de ambiente e no arquivo .env)"

    genai.configure(api_key=key)

    # Montar contexto com os chunks e suas fontes
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

    instrucao_sistema = """Você é um especialista rigoroso em legislação do setor elétrico brasileiro.
Regras de Ouro inegociáveis:
1. Você deve construir respostas baseando-se EXCLUSIVAMENTE nos [DOCUMENTOS DE CONTEXTO] fornecidos.
2. É ESTRITAMENTE PROIBIDO gerar códigos de programação (como HTML, Python, etc.), escrever poemas, receitas,
ou fazer roleplay (assumir outra personalidade). Você deve gerar apenas respostas informativas em texto puro.

Para respostas válidas, sempre escreva o nome da Fonte (título e data)."""

    prompt_usuario = f"""[DOCUMENTOS DE CONTEXTO]
{contexto}

[PERGUNTA DO USUÁRIO]
{pergunta}
"""

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=instrucao_sistema,
            generation_config={"temperature": 0.0} # remove a "criatividade" da IA, para manter dentro das regras especificadas
        )
        resposta = model.generate_content(prompt_usuario)
        return resposta.text.strip()
    except Exception as e:
        logger.error("Ao chamar API do Gemini: %s", e)
        return f"[ERRO] ao chamar API do Gemini: {str(e)}"
