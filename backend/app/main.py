from fastapi import FastAPI

from app.routes import health_routes

app = FastAPI(title="Medisafe API", version="0.1.0")

app.include_router(health_routes.router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Medisafe API is running"}