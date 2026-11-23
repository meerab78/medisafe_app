from fastapi import FastAPI

from app.core.exception_handlers import register_exception_handlers
from app.routes import (
    auth_routes,
    appointment_routes,
    caregiver_routes,
    device_routes,
    dose_routes,
    health_routes,
    internal_routes,
    medication_routes,
    medication_wizard_routes,
    options_routes,
    schedule_routes,
    refill_routes,
    user_settings_routes,
    user_routes,
)
from app.routes import report_routes

app = FastAPI(title="Medisafe API", version="0.1.0")

register_exception_handlers(app)

app.include_router(health_routes.router)
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(medication_routes.router)
app.include_router(schedule_routes.router)
app.include_router(dose_routes.router)
app.include_router(device_routes.router)
app.include_router(internal_routes.router)
app.include_router(report_routes.router)
app.include_router(options_routes.router)
app.include_router(medication_wizard_routes.router)
app.include_router(appointment_routes.router)
app.include_router(refill_routes.router)
app.include_router(user_settings_routes.router)
app.include_router(caregiver_routes.router)
@app.get("/")
def health_check():
    return {"success": True, "message": "Medisafe API is running"}