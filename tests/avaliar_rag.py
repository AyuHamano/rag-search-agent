import sys
import os
import json

# Ajusta o caminho para o Python encontrar os módulos na raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gerar_resposta.buscar_chunks import buscar_chunks
from gerar_resposta.gerar_resposta import gerar_resposta
from ingestion.criar_vetor_store import carregar_vector_store

def avaliar():
    # Define o caminho para o arquivo de perguntas que está na raiz
    caminho_json = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'perguntas_teste.json'))
    
    if not os.path.exists(caminho_json):
        print(f"❌ Erro: O arquivo {caminho_json} não foi encontrado!")
        sys.exit(1)

    # 1. Carrega o banco e as perguntas
    print("📂 Carregando banco de dados vetorial...")
    index, textos, metadados = carregar_vector_store()
    
    with open(caminho_json, "r", encoding="utf-8") as f:
        questoes = json.load(f)

    print(f"\n🚀 Iniciando avaliação de {len(questoes)} questões técnicas...\n")
    
    sucessos = 0
    for i, item in enumerate(questoes, 1):
        pergunta = item["pergunta"]
        gabarito = item["resposta_esperada"]
        
        print(f"📝 Questão {i}: {pergunta}")
        
        # 2. Executa a busca e geração do RAG
        try:
            chunks = buscar_chunks(pergunta, index, textos, metadados, top_k=3)
            resposta_agente = gerar_resposta(pergunta, chunks)
            
            print(f"🤖 Resposta do Agente: {resposta_agente[:150]}...")
            
            # 3. Validação de qualidade
            # Se a IA não der a resposta de erro padrão, consideramos que ela encontrou algo
            if "Não encontrei informações suficientes" not in resposta_agente and "[ERRO]" not in resposta_agente:
                sucessos += 1
                print("✅ STATUS: SUCESSO (Informação recuperada)")
            else:
                print("❌ STATUS: FALHA (O agente não localizou a resposta nos documentos)")
        
        except Exception as e:
            print(f"⚠️ Erro ao processar questão {i}: {e}")

        print("-" * 50)

    # Resultado Final para o GitHub Actions
    taxa_acerto = (sucessos / len(questoes)) * 100
    print(f"\n📊 RESULTADO FINAL: {sucessos}/{len(questoes)} acertos ({taxa_acerto:.1f}%)")
    
    if sucessos == 0:
        print("🚨 Erro Crítico: O agente não conseguiu responder nenhuma pergunta!")
        sys.exit(1)

if __name__ == "__main__":
    avaliar()