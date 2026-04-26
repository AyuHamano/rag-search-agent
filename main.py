from gerar_resposta.buscar_chunks import buscar_chunks
from gerar_resposta.gerar_resposta import gerar_resposta
from ingestion.criar_vetor_store import carregar_vector_store
from ingestion.ingestion import rodar_ingestion
import argparse


def main():
    parser = argparse.ArgumentParser(description="RAG Search Agent")
    parser.add_argument(
        "--mode",
        choices=["ingestion", "resposta"],
        default="resposta",
        help="Modo de execução: 'ingestion' para indexar documentos, 'resposta' para buscar e responder",
    )
    parser.add_argument(
        "--pergunta",
        type=str,
        default="Quais são as regras para conexão de microgeração distribuída?",
        help="Pergunta a ser respondida (usado apenas no modo 'resposta')",
    )
    args = parser.parse_args()
    if args.mode == "ingestion":
        client, collection_name = rodar_ingestion()
        
    elif args.mode == "resposta":
        client, collection_name = carregar_vector_store()
        pergunta = args.pergunta
        chunks = buscar_chunks(pergunta, client, collection_name, top_k=5)

        print(f"\n[RETRIEVAL] {len(chunks)} chunks encontrados:")
        for i, c in enumerate(chunks, 1):
            print(f"  {i}. {c['metadados']['titulo']} (score: {c['score']:.3f})")

        resposta = gerar_resposta(pergunta, chunks)
        print(f"\n[RESPOSTA]\n{resposta}")

        return client, collection_name


if __name__ == "__main__":
    main()
