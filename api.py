from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from agenteChatApi import consultar_agente
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
import requests

load_dotenv()
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")




# 1. Log
logging.basicConfig(
    filename=Path(__file__).parent / "webhook.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

logger = logging.getLogger(__name__)
# fin log

# leer token para instagram
logger.info("Token de Instagram configurado: %s", bool(INSTAGRAM_ACCESS_TOKEN))

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


def enviar_mensaje_instagram(destinatario_id, texto):
    url = "https://graph.instagram.com/v24.0/me/messages"

    headers = {
        "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    datos = {
        "recipient": {"id": destinatario_id},
        "message": {"text": texto}
    }

    try:
        respuesta = requests.post(
            url,
            headers=headers,
            json=datos,
            timeout=15
        )

        logger.info(
            "Envío a Instagram | HTTP %s",
            respuesta.status_code
        )
        if not respuesta.ok:
            logger.error("Detalle del error de Instagram: %s", respuesta.text)
        respuesta.raise_for_status()
        return True

    except requests.RequestException as error:
        logger.error("Error enviando a Instagram: %s", error)
        return False


@app.post("/webhook")
def recibir_webhook(datos: dict):
    print("Mensaje recibido:", datos)
    logger.info("Evento recibido en webhook | claves=%s", list(datos.keys()))
    for entrada in datos.get("entry", []):
        for evento in entrada.get("messaging", []):
            mensaje = evento.get("message", {}).get("text")
            # guarda el remitente
            remitente_id = evento.get("sender", {}).get("id")
            logger.info("ID del remitente recibido: %s", bool(remitente_id))

            if mensaje:
                logger.info("Mensaje de prueba recibido: %s", mensaje)
                respuesta = consultar_agente(mensaje)
                # enviar la respuesta al usuario en instagram
                if remitente_id:
                    enviado = enviar_mensaje_instagram(remitente_id, respuesta)
                    logger.info("Respuesta enviada a Instagram: %s", enviado)
               
                print("Respuesta del agente:", respuesta)
                logger.info("Respuesta del agente: %s", respuesta)
                return {
                    "status": "ok",
                    "respuesta": respuesta
                }

    return {"status": "ok", "respuesta": None}




from fastapi import Request, HTTPException

VERIFY_TOKEN = "turo_webhook_prueba_2026"

@app.get("/webhook")
async def verificar_webhook(request: Request):
    modo = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    desafio = request.query_params.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=desafio, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verificación fallida")


@app.get("/instagram/callback")
async def instagram_callback(request: Request):
    codigo = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return {"status": "error", "detalle": error}

    if codigo:
        return {"status": "ok", "mensaje": "Autorización recibida"}

    return {"status": "error", "mensaje": "No se recibió código"}