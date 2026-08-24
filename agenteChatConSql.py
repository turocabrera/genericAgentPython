import os
import pyodbc
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
    """OBLIGATORIO: Usa esta herramienta SIEMPRE para buscar cualquier dato, cliente, GameId, 
    registro o información en el Excel de la empresa. No intentes responder preguntas sobre el negocio 
    sin consultar esta herramienta primero.
    Entrada: términos de búsqueda o pregunta."""

    print("buscando en la base vectorial")
    docs = vectorstore.similarity_search(consulta, k=6)
    
    if not docs:
        return "No se encontró ningún registro sobre este tema en el Excel."
    
    resultado = "\n---\n".join([d.page_content for d in docs])
    return resultado



# ==========================================
# 2.1 TOOL PARA CONSULTAR PRECIO EN SQL SERVER
# ==========================================

@tool
def consultar_precio(game_id: int) -> str:
    """Consulta el precio actual de un juego por su GameId."""
    print(f"\n>>> Entré a consultar_precio")
    print(f">>> GameId recibido: {game_id}")
    print(f">>> Tipo del GameId: {type(game_id)}")

    print(f"\n💰 Consultando precio para GameId {game_id}...")

    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=Prices;"
            "Trusted_Connection=yes;"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT Price
            FROM dbo.GamePrice
            WHERE GameId = ?
            """,
            game_id
        )

        fila = cursor.fetchone()
        print(f">>> Resultado SQL: {fila}")
        conn.close()

        if fila is None:
            return f"RESULTADO_PRECIO: NO_ENCONTRADO | GameId: {game_id}"

        return (
            f"RESULTADO_PRECIO: ENCONTRADO | "
            f"GameId: {game_id} | "
            f"Precio: {fila.Price}"
        )

    except Exception as e:
        print(f">>> ERROR SQL: {e}")
        return f"RESULTADO_PRECIO: ERROR | DETALLE: {str(e)}"

tools = [buscar_en_excel, consultar_precio]

# ==========================================
# 3. MODELO GENERATIVO Y MEMORIA
# ==========================================
llm = ChatOllama(
    #model="qwen2.5:7b",
    model="llama3.2:3b",
    temperature=0.2
)

# Memoria nativa de LangGraph
memory = MemorySaver()

system_message = SystemMessage(
    content=(
           "Eres un asistente especializado en videojuegos.\n\n"

        "REGLAS OBLIGATORIAS:\n"

        "1. Si el usuario pregunta por el PRECIO de un juego usando su nombre, "
        "DEBES ejecutar primero 'buscar_en_excel' para obtener el GameId.\n"

        "2. Luego DEBES ejecutar 'consultar_precio' usando exactamente ese GameId.\n"

        "3. No respondas que no conoces el GameId sin ejecutar antes 'buscar_en_excel'.\n"

        "4. No respondas que no conoces el precio sin ejecutar antes "
        "'consultar_precio'.\n"

        "5. Para preguntas sobre género, año, empresa, juegos similares o GameId, "
        "usa 'buscar_en_excel'.\n"

        "6. Nunca inventes GameId ni precios.\n"

        "Cuando 'consultar_precio' devuelva RESULTADO_PRECIO: ENCONTRADO, "
        "DEBES informar al usuario exactamente el valor indicado en Precio. "
        "Está prohibido decir que no se encontró el precio si la herramienta "
        "devolvió RESULTADO_PRECIO: ENCONTRADO.\n"

        "Ejemplo obligatorio de comportamiento:\n"
        "Usuario: ¿Cuánto cuesta Juego X?\n"
        "Paso 1: ejecutar buscar_en_excel('Juego X')\n"
        "Paso 2: extraer el GameId del resultado\n"
        "Paso 3: ejecutar consultar_precio(GameId)\n"
        "Paso 4: responder al usuario con el precio."
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