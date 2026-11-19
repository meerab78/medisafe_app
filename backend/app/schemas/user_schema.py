from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.timezone_util import validate_timezone_name


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value):
        return validate_timezone_name(value)


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    timezone: str = Field(min_length=1, max_length=50)

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value):
        return validate_timezone_name(value)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    timezone: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)