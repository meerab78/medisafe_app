from fastapi import FastAPI

from app.core.exception_handlers import register_exception_handlers
from app.routes import (
    auth_routes,
    health_routes,
    medication_routes,
    schedule_routes,
    user_routes,
)

app = FastAPI(title="Medisafe API", version="0.1.0")

register_exception_handlers(app)

app.include_router(health_routes.router)
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(medication_routes.router)
app.include_router(schedule_routes.router)


@app.get("/")
def health_check():
    return {"success": True, "message": "Medisafe API is running"}