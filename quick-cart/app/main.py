from fastapi import FastAPI
from app.routes.webhook import router

app = FastAPI(title="WhatsApp Cart Agent")
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}