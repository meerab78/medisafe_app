from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.medication_options import (
    FOOD_INSTRUCTIONS,
    MEDICATION_FORMS,
    MEDICATION_ICONS,
    MEDICATION_ROUTES,
    get_option_values,
)

ALLOWED_MEDICATION_TYPES = get_option_values(MEDICATION_FORMS)


class MedicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    dosage: str = Field(min_length=1, max_length=100)
    medication_type: str
    route: str | None = None
    reason: str | None = Field(default=None, max_length=200)
    icon: str | None = None
    food_instruction: str = "any"
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

    @field_validator("route")
    @classmethod
    def check_route(cls, value):
        if value is None:
            return None
        value = value.strip().lower()
        if value == "":
            return None
        allowed_values = get_option_values(MEDICATION_ROUTES)
        if value not in allowed_values:
            allowed_text = ", ".join(allowed_values)
            raise ValueError("Route must be one of: " + allowed_text)
        return value

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value):
        if value is None:
            return None
        value = value.strip()
        if value == "":
            return None
        return value

    @field_validator("icon")
    @classmethod
    def check_icon(cls, value):
        if value is None:
            return None
        value = value.strip().lower()
        if value == "":
            return None
        allowed_values = get_option_values(MEDICATION_ICONS)
        if value not in allowed_values:
            allowed_text = ", ".join(allowed_values)
            raise ValueError("Icon must be one of: " + allowed_text)
        return value

    @field_validator("food_instruction")
    @classmethod
    def check_food_instruction(cls, value):
        value = value.strip().lower()
        allowed_values = get_option_values(FOOD_INSTRUCTIONS)
        if value not in allowed_values:
            allowed_text = ", ".join(allowed_values)
            raise ValueError("Food instruction must be one of: " + allowed_text)
        return value

    @model_validator(mode="after")
    def check_rules(self):
        # End date cannot be before start date
        if self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date")

        # Route is asked only for the "other" form
        if self.medication_type == "other":
            if self.route is None:
                raise ValueError("Route is required when the form is other")
        else:
            self.route = None

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
    route: str | None
    reason: str | None
    icon: str | None
    food_instruction: str
    instructions: str | None
    start_date: date
    end_date: date | None
    stock_quantity: int
    low_stock_threshold: int
    is_active: bool