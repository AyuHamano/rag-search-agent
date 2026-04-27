import sys
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------
# Configuração do Logger
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Ajusta o caminho para o Python encontrar os módulos na raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gerar_resposta.buscar_chunks import buscar_chunks
from gerar_resposta.gerar_resposta import gerar_resposta
from ingestion.criar_vetor_store import carregar_vector_store

def avaliar():
    # ---------------------------------------------------------
    # Configuração do LLM Juiz
    # ---------------------------------------------------------
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ Erro: GEMINI_API_KEY não encontrada no arquivo .env!")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    modelo_juiz = genai.GenerativeModel("gemini-2.5-flash")

    # Define o caminho para o arquivo de perguntas que está na raiz
    caminho_json = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'perguntas_teste.json'))
    
    if not os.path.exists(caminho_json):
        logger.error(f"❌ Erro: O arquivo {caminho_json} não foi encontrado!")
        sys.exit(1)

    # ---------------------------------------------------------
    # 1. Carrega o banco e as perguntas
    # ---------------------------------------------------------
    logger.info("📂 Carregando banco de dados vetorial...")
    index, textos, metadados = carregar_vector_store()
    
    with open(caminho_json, "r", encoding="utf-8") as f:
        questoes = json.load(f)

    logger.info(f"\n🚀 Iniciando avaliação de {len(questoes)} questões técnicas...\n")
    
    sucessos = 0
    
    # ---------------------------------------------------------
    # 2. Loop de Avaliação
    # ---------------------------------------------------------
    for i, item in enumerate(questoes, 1):
        pergunta = item.get("pergunta")
        gabarito = item.get("resposta_esperada")
        
        logger.info(f"📝 Questão {i}: {pergunta}")
        
        try:
            # Executa a busca e geração do RAG (O Agente respondendo)
            chunks = buscar_chunks(pergunta, index, textos, metadados, top_k=3)
            resposta_agente = gerar_resposta(pergunta, chunks)
            
            # Mostra uma prévia da resposta gerada
            logger.info(f"🤖 Resposta do Agente: {resposta_agente[:150]}...")
            
            # 3. Validação de qualidade com LLM-as-a-Judge
            if "Não encontrei informações suficientes" in resposta_agente or "[ERRO]" in resposta_agente:
                logger.warning("❌ STATUS: FALHA (O agente não localizou a informação no banco vetorial)")
            else:
                prompt_juiz = f"""
                Você é um avaliador rigoroso. Compare a resposta do Aluno com o Gabarito.
                
                PERGUNTA: {pergunta}
                GABARITO ESPERADO: {gabarito}
                RESPOSTA DO ALUNO: {resposta_agente}
                
                A resposta do aluno está semanticamente correta de acordo com o gabarito?
                Ela não precisa ter as mesmas palavras, mas deve trazer a mesma informação principal de forma correta.
                
                Responda APENAS com a palavra "CORRETO" ou "INCORRETO".
                """
                
                # Pede para a IA julgar a resposta
                resposta_juiz = modelo_juiz.generate_content(prompt_juiz, generation_config={"temperature": 0.0})
                julgamento = resposta_juiz.text.strip().upper()
                
                if "CORRETO" in julgamento and "INCORRETO" not in julgamento:
                    sucessos += 1
                    logger.info("✅ STATUS: SUCESSO (Resposta validada pelo Juiz!)")
                else:
                    logger.warning("❌ STATUS: FALHA (A resposta foi dada, mas está errada segundo o gabarito)")
        
        except Exception as e:
            logger.error(f"⚠️ Erro ao processar questão {i}: {e}")

        logger.info("-" * 50)

    # ---------------------------------------------------------
    # Resultado Final para o Console / GitHub Actions
    # ---------------------------------------------------------
    taxa_acerto = (sucessos / len(questoes)) * 100 if len(questoes) > 0 else 0
    logger.info(f"\n📊 RESULTADO FINAL: {sucessos}/{len(questoes)} acertos ({taxa_acerto:.1f}%)")

if __name__ == "__main__":
    avaliar()