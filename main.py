import os
import logging
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from openai import OpenAI

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")
MODEL_NAME = "deepseek/deepseek-v3.2"
PREFERRED_PROVIDER = "deepseek"

def call_llm_sync(user_text: str):
    """Синхронная функция для фона (выполняется в отдельном потоке)"""
    try:
        client = OpenAI(api_key=ROUTERAI_API_KEY, base_url="https://routerai.ru/api/v1")
        completion_params = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": user_text}],
            "max_tokens": 500,
            "extra_body": {
                "provider": {"only": [PREFERRED_PROVIDER]}
            }
        }
        response = client.chat.completions.create(**completion_params)
        answer = response.choices[0].message.content
        logger.info(f"✅ Ответ DeepSeek: {answer}")
    except Exception as e:
        logger.exception("❌ Ошибка в фоне")

@app.post("/")
async def alice_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    user_text = body["request"]["original_utterance"]
    logger.info(f"📥 Запрос: {user_text}")

    # Добавляем задачу в фон
    background_tasks.add_task(call_llm_sync, user_text)

    # Немедленный ответ, чтобы Алиса не таймаутила
    return {
        "version": body["version"],
        "session": body["session"],
        "response": {
            "text": "Секундочку, я думаю...",
            "end_session": False
        }
    }

@app.get("/")
async def health():
    return {"status": "ok"}
