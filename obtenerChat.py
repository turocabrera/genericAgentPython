from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings

# 1. Cargar el mismo modelo de embeddings usado al crear la base
embeddings = OllamaEmbeddings(
    # model="nomic-embed-text"
    model="bge-m3"
)

# 2. Abrir la base vectorial existente
vectorstore = Chroma(
    persist_directory="./db/games-bge-m3",                       
    embedding_function=embeddings
)

# Obtener la colección interna
coleccion = vectorstore.get()

print(f"Cantidad de documentos: {len(coleccion['documents'])}")

# print("\nPrimer documento:\n")
# print(coleccion["documents"][0])

# print("\nMetadata:\n")
# print(coleccion["metadatas"][0])

# 3. Crear el modelo de lenguaje
llm = ChatOllama(
    # model="gemma4:31b",
    # model="llama3.2:3b",
    model="qwen2.5:7b",
    temperature=0
)

# 4. Crear el prompt
prompt = ChatPromptTemplate.from_template(
    """
Respondé la pregunta utilizando únicamente el contexto recuperado
del documento.

Si la respuesta no aparece en el contexto, indicá que no encontraste
esa información en el documento.

Contexto:
{contexto}

Pregunta:
{pregunta}

Respuesta:
"""
)

# 5. Pedir una pregunta al usuario



pregunta = input("Escribí tu pregunta sobre la lista de juegos: ")

# 6. Buscar los fragmentos más relacionados
resultados = vectorstore.similarity_search(
    pregunta,
    k=6
)

# 7. Unir los fragmentos recuperados
contexto = "\n\n".join(
    documento.page_content
    for documento in resultados
)

# 8. Crear la cadena
chain = prompt | llm | StrOutputParser()

# 9. Enviar contexto y pregunta al modelo
respuesta = chain.invoke(
    {
        "contexto": contexto,
        "pregunta": pregunta
    }
)

# 10. Mostrar la respuesta
print("\nRespuesta:")
print(respuesta)