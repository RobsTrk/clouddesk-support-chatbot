from fastapi import FastAPI
from backend.api.chat import router
from backend.models.db_models import init_db

app = FastAPI(title="Autonomous Customer Support Copilot")

@app.on_event("startup")
def startup():
    init_db()

app.include_router(router)
