import requests


def gerar_resposta(pergunta: str, chunks: list[dict], api_key: str = None) -> str:
    """
    Envia pergunta + chunks recuperados para o LLM via Ollama (local e gratuito).
    O system prompt instrui o modelo a responder apenas com base nos documentos.
    """

    # Montar contexto com os chunks e suas fontes
    contexto = ""
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadados"]
        contexto += f"""
--- Fonte {i} ---
Título: {meta['titulo']}
Data: {meta['data_publicacao']}
Assunto: {meta['assunto']}
Situação: {meta['situacao']}
Trecho: {chunk['texto']}
"""

    prompt_sistema = """Você é um especialista em legislação do setor elétrico brasileiro.
Responda com base APENAS nos documentos fornecidos abaixo.
Se a resposta não estiver nos documentos, diga claramente que não encontrou a informação.
Sempre cite a fonte (título e data) ao responder."""

    prompt_completo = f"""[SYSTEM]
{prompt_sistema}

[CONTEXT]
{contexto}

[USER]
{pergunta}

[ASSISTANT]"""

    try:
        resposta = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "orca-mini", 
                "prompt": prompt_completo,
                "stream": False,
                "temperature": 0.1,
            },
            timeout=300,  # Aumentado para máquinas mais lentas
        )
        resposta.raise_for_status()
        resultado = resposta.json()
        return resultado.get("response", "Erro ao gerar resposta").strip()

    except requests.exceptions.ConnectionError:
        return "❌ Erro: Ollama não está rodando. Execute 'ollama serve' em outro terminal."
    except Exception as e:
        return f"❌ Erro ao chamar Ollama: {str(e)}"
