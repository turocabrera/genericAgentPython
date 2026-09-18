from fastapi import FastAPI
from pydantic import BaseModel
from agenteChatApi import consultar_agente

app = FastAPI()

class Consulta(BaseModel):
    mensaje: str

@app.get("/")
def inicio():
    return {"mensaje": "API del agente funcionando"}


@app.post("/consulta")
def consulta(datos: Consulta):
    respuesta = consultar_agente(datos.mensaje)
    return {"respuesta": respuesta}