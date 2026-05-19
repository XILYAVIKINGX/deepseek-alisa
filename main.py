import os
import logging
from fastapi import FastAPI, Request
from openai import OpenAI

# ================= НАСТРОЙКИ =================
# API-ключ от RouterAI (обязательно добавить переменную окружения на Render)
ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")

# Инициализация клиента OpenAI-совместимого API RouterAI
client = OpenAI(
    api_key=ROUTERAI_API_KEY,
    base_url="https://api.routerai.ru/v1"
)

# Идентификатор модели DeepSeek (уточните актуальный в личном кабинете RouterAI)
MODEL_NAME = "deepseek/deepseek-v4-pro"

# Предпочитаемый провайдер – DeepSeek
PREFERRED_PROVIDER = "deepseek"
# =============================================

app = FastAPI()

# Настройка логирования (логи будут видны в Render)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/")
async def handle_alice_request(request: Request):
    try:
        # 1. Получаем текст от Алисы
        body = await request.json()
        user_text = body["request"]["original_utterance"]
        logger.info(f"Пользователь сказал: {user_text}")

        # 2. Формируем запрос к RouterAI с указанием провайдера
        completion_params = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": user_text}],
            "max_tokens": 500,                      # ограничиваем длину ответа
            "provider": {
                "order": [PREFERRED_PROVIDER],      # сначала DeepSeek
                "allow_fallbacks": False            # не переключаться на других провайдеров при ошибке
            }
        }

        # 3. Отправляем запрос
        response = client.chat.completions.create(**completion_params)

        # 4. Извлекаем ответ нейросети
        answer = response.choices[0].message.content
        logger.info(f"Ассистент ответил: {answer}")

        # 5. Возвращаем ответ в формате, понятном Алисе
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
        # В случае любой ошибки возвращаем вежливый ответ
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
    """Эндпоинт для проверки работоспособности (нужен для пинга)"""
    return {"status": "ok"}
