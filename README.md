# RAG Search Agent - ANEEL Dataset

Sistema de busca inteligente com Retrieval Augmented Generation (RAG) para legislação ANEEL.

---
## Apresentação em Slides
| *Clique na imagem abaixo para ver os slides 👇* |
| :---: |
| <a href="https://canva.link/idwuz47d0ncr4df"><img src="rag aneel apresentação.png" width="500"></a> |
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

#### 3. Instale as dependências com docker
```bash
docker-compose up --build
docker-compose up qdrant
docker-compose up -d
```

#### 4. Configure o projeto
Edite o arquivo `const.py` conforme necessário:
```python
PDF_DIR = Path("./pdfs") 

METADATA_FILES = [
    "./dataset/biblioteca_aneel_gov_br_legislacao_2016_metadados.json",
    "./dataset/biblioteca_aneel_gov_br_legislacao_2021_metadados.json",
    "./dataset/biblioteca_aneel_gov_br_legislacao_2022_metadados.json",
]

CHUNK_SIZE = 800       
CHUNK_OVERLAP = 150     
```

#### 5. Baixe os metadados
Os arquivos JSON já estão em `dataset/`. Se precisar atualizar:

#### Passo 1: Ingestion

```bash
python -m ingestion.run --baixar-pdfs
```
- Rodar esse comando para:
    - Fazer download dos pdfs
    - Ler o conteúdo e criar os chunks
    - Fazer o parsing e salvar no QDrant

Ou, se quiser o processo, pode descompactar os chunks do "documentos_cache.zip" e e rodar o comando para salvar eles no QDrant

```bash
python -m ingestion.run 
```


#### Passo 2: Rodar a resposta da pergunta fixa
```bash
python -m streamlit run app/app.py --server.fileWatcherType none
```

## Vector embedding

```
intfloat/multilingual-e5-base
```

## Agente
- gemini-2.5-flash
