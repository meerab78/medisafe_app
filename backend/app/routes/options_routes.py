from fastapi import APIRouter

from app.schemas.options_schema import MedicationWizardResponse
from app.schemas.response_schema import ApiResponse
from app.services import options_service

router = APIRouter(prefix="/options", tags=["Options"])


@router.get("/medication-wizard", response_model=ApiResponse[MedicationWizardResponse])
def get_medication_wizard():
    # Public endpoint: it only returns options, no user data
    wizard = options_service.build_medication_wizard()
    return ApiResponse(message="Medication wizard fetched successfully", data=wizard)