import os
# from langchain_community.llms import Ollama
from langchain_ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# ==========================================
# 1. CARGAR TU BASE VECTORIAL
# ==========================================
embeddings = OllamaEmbeddings(model="bge-m3")

vectorstore = Chroma(
    persist_directory="./db/games-bge-m3", 
    embedding_function=embeddings
)

# ==========================================
# 2. CREAR LA HERRAMIENTA (TOOL) PARA EL AGENTE
# ==========================================
@tool
def buscar_en_excel(consulta: str) -> str:
    """OBLIGATORIO: Usa esta herramienta SIEMPRE para buscar cualquier dato, cliente, factura, 
    registro o información en el Excel de la empresa. No intentes responder preguntas sobre el negocio 
    sin consultar esta herramienta primero.
    Entrada: términos de búsqueda o pregunta."""

    print("buscando en la base vectorial")
    docs = vectorstore.similarity_search(consulta, k=6)
    
    if not docs:
        return "No se encontró ningún registro sobre este tema en el Excel."
    
    resultado = "\n---\n".join([d.page_content for d in docs])
    return resultado

tools = [buscar_en_excel]

# ==========================================
# 3. MODELO GENERATIVO Y MEMORIA
# ==========================================
llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.2
)

# Memoria nativa de LangGraph
memory = MemorySaver()

system_message = SystemMessage(
    content=(
        "Eres un asistente virtual corporativo útil y amable.\n"
        "REGLA OBLIGATORIA: Para responder a CUALQUIER consulta del usuario sobre "
        "juegos, genero, años de creación, empresas de video juegos DEBES ejecutar primero "
        "la herramienta 'buscar_en_excel'. No asumas ni inventes respuestas sin consultar la herramienta."
    )
)
# ==========================================
# 4. CONSTRUCCIÓN DEL AGENTE (LangGraph)
# ==========================================
# En LangGraph, 'agent' YA es el ejecutor final.
agent = create_react_agent(
    llm, 
    tools, 
    checkpointer=memory,
    prompt= system_message
    # "Eres un asistente virtual corporativo útil y amable. Responde en español usando tus herramientas cuando sea necesario."
)

# Identificador de la sesión de chat (para que mantenga la memoria del usuario)
config = {"configurable": {"thread_id": "sesion_excel_1"}}

# ==========================================
# 5. BUCLE DE CHAT INTERACTIVO (CLI)
# ==========================================
print("\n🤖 ¡Agente de Ollama Iniciado! Escribe 'salir' para finalizar.\n")

while True:
    pregunta_usuario = input("\nTú: ")
    if pregunta_usuario.lower() in ["salir", "exit", "quit"]:
        print("🤖 ¡Hasta luego!")
        break
        
    # Invocamos el agente con el formato de mensajes de LangGraph
    resultado = agent.invoke(
        {"messages": [("user", pregunta_usuario)]},
        config=config
    )
    
    # Extraemos el último mensaje de la respuesta (que es la respuesta final del modelo)
    respuesta_final = resultado["messages"][-1].content
    
    print(f"\n🤖 Agente: {respuesta_final}")