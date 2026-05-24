from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
import uvicorn
import logging

# Load environment variables from .env file before anything else
load_dotenv()

from agent import process_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevOps Autohealing Agent")

@app.get("/")
async def root():
    return {"message": "DevOps Autohealing Agent is running! Send alerts to POST /webhook"}

@app.get("/webhook")
async def get_webhook():
    return {"message": "The webhook endpoint only accepts POST requests from Prometheus Alertmanager."}

@app.post("/webhook")
async def prometheus_webhook(request: Request):
    """
    Receives webhook alerts from Prometheus Alertmanager.
    """
    payload = await request.json()
    logger.info(f"Received Webhook Payload: {payload}")
    
    # Prometheus/Alertmanager sends a list of alerts
    alerts = payload.get("alerts", [])
    
    for alert in alerts:
        if alert.get("status") == "firing":
            logger.info("Processing firing alert...")
            # Hand off to the LLM agent to analyze and resolve
            await process_alert(alert)

    return {"status": "success", "message": "Alerts processed"}

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host=host, port=port, reload=True)
