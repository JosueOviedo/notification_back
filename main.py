import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import firebase_admin
from firebase_admin import credentials, messaging


# --- Inicializar Firebase Admin SDK ---
try:
    credentials_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK inicializado correctamente.")
    else:
        print("Firebase Admin SDK ya estaba inicializado.")

except Exception as e:
    print(f"⚠️ ERROR al iniciar Firebase Admin SDK ({credentials_path})")
    print(f"Detalle: {e}")


# --- Modelo JSON esperado ---
class NotificationRequest(BaseModel):
    token: Optional[str] = None
    topic: Optional[str] = None
    title: str = "Promoción Especial"
    body: str = "¡Gran descuento disponible!"
    imageUrl: str = "https://picsum.photos/1024/512"
    promoId: str = "PROMO_001"


# --- FastAPI ---
app = FastAPI(
    title="Android FCM Push Sender",
    description="Backend para enviar notificaciones Push SOLO Android con imagen (BigPicture)."
)


# --- Endpoint principal ---
@app.post("/send", summary="Enviar notificación Push a Android")
async def send_push_notification(request: NotificationRequest):
    if not request.token and not request.topic:
        raise HTTPException(status_code=400, detail="Debes proporcionar 'token' o 'topic'.")

    # Payload de datos
    data_payload = {
        "promoId": request.promoId,
        "imageUrl": request.imageUrl,
        "click_action": "FLUTTER_NOTIFICATION_CLICK"
    }

    # Construcción del mensaje SOLO para Android
    message_payload = messaging.Message(
        data=data_payload,
        notification=messaging.Notification(
            title=request.title,
            body=request.body
        ),
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                image=request.imageUrl,  # BigPicture
                priority="high"
            )
        )
    )

    try:
        if request.token:
            message_payload.token = request.token
            response = messaging.send(message_payload)
            destination = request.token

        else:
            message_payload.topic = request.topic
            response = messaging.send(message_payload)
            destination = request.topic

        return {
            "status": "success",
            "message_id": response,
            "sent_to": destination
        }

    except Exception as e:
        error_message = f"Error enviando notificación: {e}"
        print("❌", error_message)
        raise HTTPException(status_code=500, detail=error_message)


# Endpoint para verificar el servidor
@app.get("/")
def root():
    return {"status": "ok", "message": "Servidor para Android listo."}
