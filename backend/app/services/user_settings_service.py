from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.user_settings_options import SNOOZE_OPTIONS
from app.models.user_model import User
from app.models.user_settings_model import UserSettings
from app.repositories import user_settings_repository
from app.schemas.user_settings_schema import UserSettingsResponse, UserSettingsUpdate


def get_or_create_settings(db: Session, user: User):
    user_id = user.id

    settings = user_settings_repository.get_settings_by_user(db, user_id)
    if settings is not None:
        return settings

    # First time: create the row. The model gives the default values.
    new_settings = UserSettings(user_id=user_id)
    try:
        return user_settings_repository.save_settings(db, new_settings)
    except IntegrityError:
        # Another request created the row at the same moment, so we read it again
        user_settings_repository.rollback(db)
        return user_settings_repository.get_settings_by_user(db, user_id)


def make_response(settings: UserSettings):
    return UserSettingsResponse(
        reminders_enabled=settings.reminders_enabled,
        snooze_minutes=settings.snooze_minutes,
        refill_alerts_enabled=settings.refill_alerts_enabled,
        snooze_options=SNOOZE_OPTIONS,
    )


def get_settings(db: Session, user: User):
    settings = get_or_create_settings(db, user)
    return make_response(settings)


def update_settings(db: Session, user: User, data: UserSettingsUpdate):
    settings = get_or_create_settings(db, user)

    settings.reminders_enabled = data.reminders_enabled
    settings.snooze_minutes = data.snooze_minutes
    settings.refill_alerts_enabled = data.refill_alerts_enabled

    saved = user_settings_repository.save_settings(db, settings)
    return make_response(saved)