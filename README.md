# RAG Search Agent - ANEEL Dataset

Sistema de busca inteligente com Retrieval Augmented Generation (RAG) para legislação ANEEL.

---

## Como Rodar

#### 1. Clone o repositório
```bash
git clone <seu-repo-url>
cd rag-search-agent
```

#### 2. Crie um ambiente virtual
```bash
# Windows (PowerShell)
python -m venv venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process 
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instale as dependências
```bash
pip install --upgrade pip
pip install pdfplumber pymupdf langchain langchain-community
pip install sentence-transformers faiss-cpu
pip install openai cloudscraper requests
pip install chromadb  # para vector store
```

#### 4. Configure o projeto
Edite o arquivo `const.py` conforme necessário:
```python
PDF_DIR = Path("./pdfs") 

METADATA_FILES = [
    "./dados_grupo_estudos/biblioteca_aneel_gov_br_legislacao_2016_metadados-curto.json",
    # Descomente para adicionar mais metadados
    # "./dados_grupo_estudos/biblioteca_aneel_gov_br_legislacao_2021_metadados.json",
    # "./dados_grupo_estudos/biblioteca_aneel_gov_br_legislacao_2022_metadados.json",
]

CHUNK_SIZE = 800        # Caracteres por chunk
CHUNK_OVERLAP = 150     # Sobreposição entre chunks
IGNORAR_REVOGADOS = False  # Filtrar documentos revogados
```

#### 5. Baixe os metadados
Os arquivos JSON já estão em `dados_grupo_estudos/`. Se precisar atualizar:
```bash
# Coloque os arquivos JSON em dados_grupo_estudos/
# Formato esperado: biblioteca_aneel_gov_br_legislacao_AAAA_metadados.json
```

### Como Executar

#### Opção 1: Pipeline completo
```bash
python parsing.py
```

#### Opção 2: Apenas parsing e ingestion
```bash
python parsing.py
```

## Parsing:

- Mapear o dataset e ver quais pdf's possuem tabela:
   - Possuem tabela --> utilizar o pdfplumber
   - Possuem apenas texto corrido --> pymupdf
- juntar tudo no final com seus respectivos metados

## Chunking:

- Usar Langchain, que é mais popular

## Vector embedding

- modelos: nomic-embed-text, mxbai-embed-large, paraphrase-multilingual-MiniLM-L12-v2
- Salva no Chroma

## Retrieval - Busca inteligente
- busca semântica: CrossEncoder

## Agente
- Implementar o Agente LLM usando LangChain/LlamaIndex
- Crie um arquivo .env e coloque sua chave API do Gemini conforme o .env.example

Entrar no ambiente venv
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process 
.\venv\Scripts\Activate.ps1
```

Baixar streamlit
```
pip install streamlit
```
Rodar o comando
```
python -m streamlit run app/app.py --server.fileWatcherType none
```
