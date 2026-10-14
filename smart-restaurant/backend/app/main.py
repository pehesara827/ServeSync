from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import kitchen, orders
from .iot.mqtt_client import connect_mqtt, disconnect_mqtt, mqtt_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-connect so the first COMPLETED order doesn't pay the CONNACK race.
    # Fail-open on purpose: broker downtime must never stop the API booting.
    connect_mqtt()
    try:
        yield
    finally:
        disconnect_mqtt()


# Creates the API application served by Uvicorn.
app = FastAPI(title="Smart Restaurant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(kitchen.router)


@app.get("/health")
def health():
    """Reports that the backend process is responding."""
    return {"status": "ok"}


@app.get("/health/mqtt")
def health_mqtt():
    """Reports effective broker config + live connection state.

    Lets ops distinguish 'backend down' from 'Mosquitto down / wrong
    MQTT_BROKER_HOST'. Returns 200 always; check `connected` flag.
    """
    return {"status": "ok", "mqtt": mqtt_status()}
