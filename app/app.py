import streamlit as st

from ingestion.criar_vetor_store import carregar_vector_store
from gerar_resposta.buscar_chunks import buscar_chunks
from gerar_resposta.gerar_resposta import gerar_resposta

# comando usado pra rodar: python -m streamlit run app/app.py --server.fileWatcherType none

@st.cache_resource
def carregar_dados():
    index, textos, metadados = carregar_vector_store()
    return index, textos, metadados

index, textos, metadados = carregar_dados()

st.title("RAG Search Agent - ANEEL Dataset")
st.markdown("Sistema de busca inteligente com Retrieval Augmented Generation (RAG) para legislação ANEEL.")

if "mensagens" not in st.session_state:
    # cria uma lista vazia de mensagens, se nao tiver nenhuma mensagem
    st.session_state.mensagens = []

# exibe o historico de mensagens
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):  # "role": user ou assistant (IA)
        st.markdown(msg["content"])

pergunta = st.chat_input("Pergunte algo sobre Geração Distribuída...")

if pergunta:
    # exibe a pergunta
    with st.chat_message("user"):
        st.markdown(pergunta)
    # salva a pergunta na memoria
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    
    # formulacao da resposta usando o banco de dados
    with st.spinner("Pesquisando na biblioteca da ANEEL..."):
        
        # busca de chunks
        chunks_encontrados = buscar_chunks(pergunta, index, textos, metadados, top_k=5)
        
        # formula a resposta com a IA
        resposta_final = gerar_resposta(pergunta, chunks_encontrados)

    # exibe a resposta da IA
    with st.chat_message("assistant"):
        st.markdown(resposta_final)
    # salva a resposta da IA na memoria
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})

