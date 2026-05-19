import os
import logging
from fastapi import FastAPI, Request
from openai import OpenAI

# ================= НАСТРОЙКИ =================
ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")

client = OpenAI(
    api_key=ROUTERAI_API_KEY,
    base_url="https://routerai.ru/api/v1"
)

# Используем быструю и стабильную модель
# Альтернативные варианты: "google/gemini-2.0-flash-lite-001:free"
MODEL_NAME = "deepseek/deepseek-chat"
# =============================================

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/")
async def handle_alice_request(request: Request):
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]
        logger.info(f"Пользователь сказал: {user_text}")

        # Упрощаем параметры, убирая привязку к конкретному провайдеру
        completion_params = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": user_text}],
            "max_tokens": 500,
        }

        response = client.chat.completions.create(**completion_params)
        answer = response.choices[0].message.content
        logger.info(f"Ассистент ответил: {answer}")

        return {
            "version": body["version"],
            "session": body["session"],
            "response": {
                "text": answer,
                "end_session": False
            }
        }

    except Exception as e:
        logger.exception("Ошибка при обработке запроса")
        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {
                "text": "Извините, произошла ошибка. Попробуйте ещё раз.",
                "end_session": False
            }
        }


@app.get("/")
async def health_check():
    return {"status": "ok"}
