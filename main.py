import os
import logging
import time
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")
MODEL_NAME = "deepseek/deepseek-v4-pro"   # или попробуйте meta-llama/llama-3.2-3b-instruct:free
PREFERRED_PROVIDER = "deepseek"

@app.post("/")
async def alice_webhook(request: Request):
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]
        logger.info(f"Запрос: {user_text}")

        start = time.time()
        client = OpenAI(api_key=ROUTERAI_API_KEY, base_url="https://routerai.ru/api/v1")
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": user_text}],
            max_tokens=200,
            extra_body={"provider": {"only": [PREFERRED_PROVIDER]}},
            timeout=4.0
        )
        elapsed = time.time() - start
        answer = completion.choices[0].message.content
        logger.info(f"Ответ (за {elapsed:.2f} сек): {answer[:100]}...")

        return {
            "version": body["version"],
            "session": body["session"],
            "response": {"text": answer, "end_session": False}
        }
    except Exception as e:
        logger.exception("Ошибка")
        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {"text": "Ошибка, попробуйте ещё.", "end_session": False}
        }

@app.get("/")
async def health():
    return {"status": "ok"}
