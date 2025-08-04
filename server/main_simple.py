import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

# Инициализация Sentry
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration(auto_enabling_integrations=False)],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        send_default_pii=True,
    )
    print(f"Sentry initialized with DSN: {sentry_dsn}")
else:
    print("Sentry DSN not found, Sentry not initialized")

app = FastAPI(title="EduAnalytics API - Simple Test")

@app.get("/")
async def root():
    return {"message": "EduAnalytics API - Simple Test for Sentry"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/sentry/test")
async def test_sentry():
    """Тестовый эндпоинт для проверки Sentry"""
    try:
        # Намеренно вызываем ошибку
        result = 1 / 0
        return {"result": result}
    except Exception as e:
        # Отправляем ошибку в Sentry
        sentry_sdk.capture_exception(e)
        return JSONResponse(
            status_code=500,
            content={"message": "Test error sent to Sentry", "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)