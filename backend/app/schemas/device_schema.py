from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_PLATFORMS = ["android", "ios", "web"]


class DeviceRegister(BaseModel):
    fcm_token: str = Field(min_length=10, max_length=500)
    platform: str

    @field_validator("fcm_token")
    @classmethod
    def remove_extra_spaces(cls, value):
        return value.strip()

    @field_validator("platform")
    @classmethod
    def check_platform(cls, value):
        # Make it lower case, then check it is in the allowed list
        value = value.strip().lower()
        if value not in ALLOWED_PLATFORMS:
            allowed_text = ", ".join(ALLOWED_PLATFORMS)
            raise ValueError("Platform must be one of: " + allowed_text)
        return value


class DeviceUnregister(BaseModel):
    fcm_token: str = Field(min_length=10, max_length=500)

    @field_validator("fcm_token")
    @classmethod
    def remove_extra_spaces(cls, value):
        return value.strip()


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    created_at: datetime