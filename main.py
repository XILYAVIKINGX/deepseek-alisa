import os
import logging
import socket
import requests
from fastapi import FastAPI, Request
from openai import OpenAI

# ================= НАСТРОЙКИ =================
ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")

client = OpenAI(
    api_key=ROUTERAI_API_KEY,
    base_url="https://routerai.ru/api/v1"
)

MODEL_NAME = "deepseek/deepseek-v3.2"   # уточните актуальное имя модели в RouterAI
PREFERRED_PROVIDER = "deepseek"
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

        completion_params = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": user_text}],
            "max_tokens": 500,
            "extra_body": {
                "provider": {
                    "order": [PREFERRED_PROVIDER],
                    "allow_fallbacks": False
                }
            }
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
    """Диагностический эндпоинт — показывает DNS, HTTP и клиентскую связность"""
    diag = {"status": "ok", "diagnostics": {}}

    # 1. DNS резолвинг
    try:
        host = "routerai.ru"
        addrs = socket.getaddrinfo(host, 443)
        ips = list(set([addr[4][0] for addr in addrs]))
        diag["diagnostics"]["dns"] = {"host": host, "resolved_ips": ips}
    except Exception as e:
        diag["diagnostics"]["dns"] = {"error": str(e)}
        diag["status"] = "degraded"

    # 2. Прямой HTTP-запрос через requests
    try:
        test_url = "https://routerai.ru/api/v1/models"
        r = requests.get(test_url, timeout=10)
        diag["diagnostics"]["http_models"] = {
            "url": test_url,
            "status": r.status_code,
            "success": r.status_code == 200
        }
    except Exception as e:
        diag["diagnostics"]["http_models"] = {"error": str(e)}
        diag["status"] = "unhealthy"

    # 3. Проверка через OpenAI клиент (минимальный запрос)
    try:
        test_client = OpenAI(
            api_key=ROUTERAI_API_KEY,
            base_url="https://routerai.ru/api/v1",
            timeout=10.0
        )
        resp = test_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )
        diag["diagnostics"]["openai_client"] = {
            "success": True,
            "response_id": resp.id
        }
    except Exception as e:
        diag["diagnostics"]["openai_client"] = {"error": str(e)}
        diag["status"] = "degraded"

    return diag
