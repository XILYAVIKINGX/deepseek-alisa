import logging
from fastapi import FastAPI, Request

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/")
async def handle_alice_request(request: Request):
    body = await request.json()
    user_text = body["request"]["original_utterance"]
    logger.info(f"Получено: {user_text}")

    # Мгновенный ответ
    return {
        "version": body["version"],
        "session": body["session"],
        "response": {
            "text": f"Вы сказали: {user_text}",
            "end_session": False
        }
    }

@app.get("/")
async def health():
    return {"status": "ok"}
