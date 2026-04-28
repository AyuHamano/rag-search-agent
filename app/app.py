from sentence_transformers import SentenceTransformer
import streamlit as st

from ingestion.criar_vetor_store import carregar_vector_store
from gerar_resposta.buscar_chunks import buscar_chunks
from gerar_resposta.gerar_resposta import gerar_resposta

@st.cache_resource
def carregar_dados():
    client, collection_name = carregar_vector_store()
    modelo = SentenceTransformer(
        "intfloat/multilingual-e5-base"
    )
    print(f"[INFO] Qdrant carregado — collection: {collection_name}")
    return client, collection_name, modelo

client, collection_name, modelo = carregar_dados()

st.title("RAG Search Agent - ANEEL Dataset")
st.markdown("Sistema de busca inteligente com Retrieval Augmented Generation (RAG) para legislação ANEEL.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Pergunte algo sobre Geração Distribuída...")

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    with st.spinner("Pesquisando na biblioteca da ANEEL..."):
        chunks_encontrados = buscar_chunks(pergunta, client, collection_name, modelo, top_k=10)
        print(f"[INFO] {len(chunks_encontrados)} chunks encontrados para a pergunta: '{pergunta}'")
        print(f"[DEBUG] Chunks encontrados: {[c['metadados']['titulo'] for c in chunks_encontrados]}")
        resposta_final = gerar_resposta(pergunta, chunks_encontrados)

    with st.chat_message("assistant"):
        st.markdown(resposta_final)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})