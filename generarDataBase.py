import pandas as pd
# from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# 1. Leer el PDF
# loader = PyPDFLoader("./origenes/listadoJuegos.xlsx")
# documentos = loader.load()

# 2. Leers el archivo con pandas
df = pd.read_excel("./origenes/listadoJuegos.xlsx")
firstColumns = df.columns[:14]
df['datavectorial'] = df[firstColumns].apply(
    lambda row: " | ".join([f"{col}: {row[col]}" for col in firstColumns if pd.notna(row[col])]),
    axis=1
)
# 2. Indicas cuál columna contiene el texto principal que quieres vectorizar
loader = DataFrameLoader(df, page_content_column="datavectorial")
documentos = loader.load()

print(f"Páginas leídas: {len(documentos)}")

# 2. Dividir en chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(documentos)

print(f"Cantidad de chunks: {len(chunks)}")

# 3. Modelo de embeddings
embeddings = OllamaEmbeddings(
    # model="nomic-embed-text"
    model="bge-m3"
    
)

# 4. Crear la base vectorial
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    # persist_directory="./db/games
    persist_directory="./db/games-bge-m3"
)

print("Embeddings creados correctamente.")


# PDF
#  ↓
# PyPDFLoader
#  ↓
# Documentos
#  ↓
# TextSplitter
#  ↓
# Chunks
#  ↓
# OllamaEmbeddings
#  ↓
# Vectores
#  ↓
# ChromaDB