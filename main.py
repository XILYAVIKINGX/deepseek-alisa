import os
import logging
from fastapi import FastAPI, Request
import requests
import json

app = FastAPI()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Используем модель, которая точно существует (проверено вручную)
MODEL_NAME = "openrouter/free"  # альтернатива DeepSeek

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/")
async def main(request: Request):
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]
        logger.info(f"User said: {user_text}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": user_text}],
            "max_tokens": 500,
            # Явно отключаем инструменты и используем JSON mode
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
            return {
                "version": body["version"],
                "session": body["session"],
                "response": {
                    "text": "Сервис временно недоступен. Попробуйте позже.",
                    "end_session": False
                }
            }

        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            logger.error(f"No choices: {data}")
            return {
                "version": body["version"],
                "session": body["session"],
                "response": {
                    "text": "Нейросеть не смогла ответить.",
                    "end_session": False
                }
            }

        answer = data["choices"][0]["message"]["content"]
        
        # JSON mode возвращает объект, нужно извлечь текст (можно оставить как есть)
        try:
            # Если ответ в JSON, можно взять поле text
            answer_json = json.loads(answer)
            answer = answer_json.get("text", answer)
        except:
            pass

        return {
            "version": body["version"],
            "session": body["session"],
            "response": {
                "text": answer,
                "end_session": False
            }
        }

    except Exception as e:
        logger.exception("Unexpected error")
        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {
                "text": "Ошибка. Попробуйте ещё раз.",
                "end_session": False
            }
        }

@app.get("/")
async def health():
    return {"status": "ok"}
