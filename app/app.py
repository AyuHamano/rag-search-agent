import streamlit as st

from ingestion.criar_vetor_store import carregar_vector_store
from gerar_resposta.buscar_chunks import buscar_chunks
from gerar_resposta.gerar_resposta import gerar_resposta

# comando usado pra rodar: python -m streamlit run app/app.py --server.fileWatcherType none

@st.cache_resource
def carregar_dados():
    client, collection_name = carregar_vector_store()
    print(f"[INFO] Qdrant carregado — collection: {collection_name}")
    return client, collection_name

client, collection_name = carregar_dados()

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
        chunks_encontrados = buscar_chunks(pergunta, client, collection_name, top_k=5)
        resposta_final = gerar_resposta(pergunta, chunks_encontrados)

    with st.chat_message("assistant"):
        st.markdown(resposta_final)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})