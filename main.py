from gerar_resposta import buscar_chunks, gerar_resposta
from ingestion.criar_vetor_store import carregar_vector_store
from ingestion.ingestion import rodar_ingestion

def main(mode = 'ingestion'):
    if(mode == 'ingestion'):
        rodar_ingestion()
    else:
        index, textos, metadados = carregar_vector_store()
        pergunta = "Quais são as regras para conexão de microgeração distribuída?"
        chunks = buscar_chunks(pergunta, index, textos, metadados, top_k=5)

    print(f"\n[RETRIEVAL] {len(chunks)} chunks encontrados:")
    for i, c in enumerate(chunks, 1):
        print(f"  {i}. {c['metadados']['titulo']} (score: {c['score']:.3f})")

    resposta = gerar_resposta(pergunta, chunks)
    print(f"\n[RESPOSTA]\n{resposta}")

    return index, textos, metadados


if __name__ == "__main__":

    main()
