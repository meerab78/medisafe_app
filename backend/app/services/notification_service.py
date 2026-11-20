import logging

import firebase_admin
from firebase_admin import credentials, exceptions, messaging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import device_repository

logger = logging.getLogger(__name__)


def get_firebase_app():
    # Start Firebase only once, then reuse it
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        return firebase_admin.initialize_app(cred)


def send_push_to_token(fcm_token: str, title: str, body: str, data: dict | None = None) -> str:
    if not settings.fcm_enabled:
        logger.info("FCM is disabled. Push notification skipped.")
        return "disabled"

    # FCM data values must be text
    message_data = {}
    if data is not None:
        for key in data:
            message_data[key] = str(data[key])

    try:
        get_firebase_app()
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(title=title, body=body),
            data=message_data,
        )
        messaging.send(message)
        return "sent"
    except messaging.UnregisteredError:
        return "invalid_token"
    except messaging.SenderIdMismatchError:
        return "invalid_token"
    except (exceptions.FirebaseError, ValueError, OSError):
        logger.exception("Failed to send push notification")
        return "failed"


def send_push_to_user(
    db: Session, user_id: int, title: str, body: str, data: dict | None = None
) -> int:
    tokens = device_repository.list_fcm_tokens_for_user(db, user_id)
    sent_count = 0

    for token in tokens:
        result = send_push_to_token(token, title, body, data)
        if result == "sent":
            sent_count = sent_count + 1
        elif result == "invalid_token":
            device_repository.remove_fcm_token(db, token)

    return sent_count