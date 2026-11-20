from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schedule_model import Schedule, ScheduleTime


def get_schedule_by_medication(db: Session, medication_id: int):
    query = select(Schedule).where(Schedule.medication_id == medication_id)
    return db.scalar(query)


def get_times_by_schedule(db: Session, schedule_id: int):
    query = (
        select(ScheduleTime)
        .where(ScheduleTime.schedule_id == schedule_id)
        .order_by(ScheduleTime.time_of_day)
    )
    return list(db.scalars(query).all())


def add_schedule(db: Session, schedule: Schedule):
    db.add(schedule)
    # flush gives the schedule an id without saving permanently yet
    db.flush()
    return schedule


def add_schedule_time(db: Session, schedule_time: ScheduleTime):
    db.add(schedule_time)


def delete_times_by_schedule(db: Session, schedule_id: int):
    times = get_times_by_schedule(db, schedule_id)
    for schedule_time in times:
        db.delete(schedule_time)
    db.flush()


def delete_schedule(db: Session, schedule: Schedule):
    db.delete(schedule)


def commit(db: Session):
    db.commit()