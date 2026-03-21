import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# URL API OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Читаем ключ из переменной окружения
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ✅ ИСПРАВЛЕНО: используем актуальное название бесплатной модели DeepSeek-V3
MODEL_NAME = "deepseek/deepseek-r1"

# Настройка логирования
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

        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": user_text}],
                "max_tokens": 500
            },
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
            return {
                "version": body["version"],
                "session": body["session"],
                "response": {
                    "text": "Извините, сервис временно недоступен. Попробуйте позже.",
                    "end_session": False
                }
            }

        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            logger.error(f"No choices in response: {data}")
            if "error" in data:
                error_msg = data["error"].get("message", "Неизвестная ошибка")
                answer = f"Ошибка API: {error_msg}"
            else:
                answer = "Нейросеть не смогла сформулировать ответ."
            return {
                "version": body["version"],
                "session": body["session"],
                "response": {
                    "text": answer,
                    "end_session": False
                }
            }

        answer = data["choices"][0]["message"]["content"]

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
                "text": "Произошла внутренняя ошибка. Попробуйте ещё раз.",
                "end_session": False
            }
        }

@app.get("/")
async def health():
    return {"status": "ok"}
