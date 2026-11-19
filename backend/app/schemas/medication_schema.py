from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_MEDICATION_TYPES = [
    "tablet",
    "capsule",
    "syrup",
    "injection",
    "drops",
    "inhaler",
    "cream",
    "other",
]


class MedicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    dosage: str = Field(min_length=1, max_length=100)
    medication_type: str
    instructions: str | None = None
    start_date: date
    end_date: date | None = None
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)

    @field_validator("name", "dosage")
    @classmethod
    def remove_extra_spaces(cls, value):
        # Remove spaces from both sides and reject empty text
        value = value.strip()
        if value == "":
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("medication_type")
    @classmethod
    def check_medication_type(cls, value):
        # Make it lower case, then check it is in the allowed list
        value = value.strip().lower()
        if value not in ALLOWED_MEDICATION_TYPES:
            allowed_text = ", ".join(ALLOWED_MEDICATION_TYPES)
            raise ValueError("Medication type must be one of: " + allowed_text)
        return value

    @model_validator(mode="after")
    def check_dates(self):
        # End date cannot be before start date
        if self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date")
        return self


class MedicationUpdate(MedicationCreate):
    # Same fields as create, plus is_active (so a deleted medication can be restored)
    is_active: bool = True


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dosage: str
    medication_type: str
    instructions: str | None
    start_date: date
    end_date: date | None
    stock_quantity: int
    low_stock_threshold: int
    is_active: bool