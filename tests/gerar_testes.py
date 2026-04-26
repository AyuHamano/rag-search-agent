import random
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# Importa a sua função que carrega os dados já mastigados
from ingestion.criar_vetor_store import carregar_vector_store

load_dotenv()

def gerar_dataset_de_teste(quantidade=5):
    print("Carregando banco de dados...")
    _, textos, metadados = carregar_vector_store()
    
    # Filtra chunks muito pequenos que não rendem boas perguntas
    chunks_validos = [i for i, t in enumerate(textos) if len(t) > 300]
    
    # Sorteia os chunks
    indices_sorteados = random.sample(chunks_validos, min(quantidade, len(chunks_validos)))
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    dataset_teste = []
    
    print(f"Gerando {quantidade} perguntas baseadas nos documentos...\n")
    
    for idx in indices_sorteados:
        texto_base = textos[idx]
        meta = metadados[idx]
        
        prompt = f"""
        Você é um elaborador de provas sobre a legislação da ANEEL.
        Leia o [TEXTO BASE] abaixo e crie UMA pergunta técnica e complexa cuja resposta esteja EXATAMENTE neste texto.
        
        Retorne APENAS um objeto JSON válido neste formato:
        {{
            "pergunta": "Sua pergunta aqui",
            "resposta_esperada": "A resposta exata baseada no texto"
        }}
        
        [TEXTO BASE]:
        {texto_base}
        """
        
        try:
            resposta = model.generate_content(prompt, generation_config={"temperature": 0.2})
            
            # Limpa a formatação markdown (```json) que o Gemini costuma colocar
            texto_limpo = resposta.text.replace('```json', '').replace('```', '').strip()
            qa_pair = json.loads(texto_limpo)
            
            # Adiciona de onde a informação saiu
            qa_pair["fonte"] = meta.get("titulo", "Título não encontrado")
            qa_pair["arquivo"] = meta.get("arquivo", "Arquivo não encontrado")
            
            dataset_teste.append(qa_pair)
            print(f"✅ Pergunta gerada para a fonte: {qa_pair['fonte']}")
            
        except Exception as e:
            print(f"❌ Erro ao gerar pergunta para um chunk: {e}")
            
    # Salva o resultado
    with open("perguntas_teste.json", "w", encoding="utf-8") as f:
        json.dump(dataset_teste, f, ensure_ascii=False, indent=4)
        
    print("\n[SUCESSO] Arquivo 'perguntas_teste.json' gerado com sucesso!")

if __name__ == "__main__":
    gerar_dataset_de_teste(quantidade=10) # Altere a quantidade como preferir