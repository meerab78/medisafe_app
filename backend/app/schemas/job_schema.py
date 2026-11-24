from datetime import datetime

from pydantic import BaseModel


class MissedDoseJobResponse(BaseModel):
    missed_count: int
    checked_before: datetime
    # How many push messages were delivered to caregivers
    alerts_sent: int = 0