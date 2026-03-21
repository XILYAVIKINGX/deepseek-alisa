import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Настройка логирования (логи будут видны в Render)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/")
async def main(request: Request):
    try:
        # Получаем текст от пользователя из запроса Алисы
        body = await request.json()
        user_text = body["request"]["original_utterance"]
        logger.info(f"User said: {user_text}")

        # Отправляем запрос к DeepSeek API
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=30
        )

        # Проверяем статус HTTP
        if response.status_code != 200:
            logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
            return {
                "version": body["version"],
                "session": body["session"],
                "response": {
                    "text": "Извините, произошла ошибка при обращении к нейросети. Попробуйте позже.",
                    "end_session": False
                }
            }

        data = response.json()
        logger.info(f"DeepSeek response: {data}")

        # Проверяем, есть ли поле choices
        if "choices" not in data or not data["choices"]:
            # Если есть поле error — выводим его
            if "error" in data:
                error_msg = data["error"].get("message", "Неизвестная ошибка API")
                logger.error(f"DeepSeek API returned error: {error_msg}")
                answer = f"Ошибка API: {error_msg}"
            else:
                logger.error(f"Unexpected response format: {data}")
                answer = "Нейросеть вернула ответ в неожиданном формате."
            # Возвращаем сообщение об ошибке в Алису
            return {
                "version": body["version"],
                "session": body["session"],
                "response": {
                    "text": answer,
                    "end_session": False
                }
            }

        # Безопасно извлекаем текст ответа
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
        logger.exception("Unexpected error in webhook")
        # В случае любой другой ошибки возвращаем вежливый ответ
        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {
                "text": "Извините, произошла внутренняя ошибка. Попробуйте ещё раз.",
                "end_session": False
            }
        }

# Опционально: GET эндпоинт для проверки здоровья (чтобы пинговать)
@app.get("/")
async def health():
    return {"status": "ok"}
