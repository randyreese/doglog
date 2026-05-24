from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional
import models
from database import get_db

router = APIRouter()


class DogStatus(BaseModel):
    id: int
    name: str
    track_pee: bool
    last_pee: Optional[datetime]
    last_poo: Optional[datetime]
    poo_count_today: int


class StatusResponse(BaseModel):
    dogs: list[DogStatus]


@router.get("/status/", response_model=StatusResponse)
def get_status(db: Session = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time())
    dogs = db.query(models.Dog).filter(models.Dog.active == True).order_by(models.Dog.name).all()

    result = []
    for dog in dogs:
        last_pee = None
        if dog.track_pee:
            row = (
                db.query(models.PeePooEvent)
                .filter(models.PeePooEvent.dog_id == dog.id, models.PeePooEvent.type == 'pee')
                .order_by(models.PeePooEvent.timestamp.desc())
                .first()
            )
            last_pee = row.timestamp if row else None

        last_poo_row = (
            db.query(models.PeePooEvent)
            .filter(models.PeePooEvent.dog_id == dog.id, models.PeePooEvent.type == 'poo')
            .order_by(models.PeePooEvent.timestamp.desc())
            .first()
        )
        last_poo = last_poo_row.timestamp if last_poo_row else None

        poo_count = (
            db.query(models.PeePooEvent)
            .filter(
                models.PeePooEvent.dog_id == dog.id,
                models.PeePooEvent.type == 'poo',
                models.PeePooEvent.timestamp >= today_start,
            )
            .count()
        )

        result.append(DogStatus(
            id=dog.id,
            name=dog.name,
            track_pee=dog.track_pee,
            last_pee=last_pee,
            last_poo=last_poo,
            poo_count_today=poo_count,
        ))

    return StatusResponse(dogs=result)


# ── History ────────────────────────────────────────────────────────────────────

class DogInfo(BaseModel):
    id: int
    name: str
    track_pee: bool

class DayCount(BaseModel):
    pee: int
    poo: int

class DaySummary(BaseModel):
    date: str   # YYYY-MM-DD
    label: str  # Mon/Tue/…/Sun

    counts: dict[str, DayCount]  # keyed by str(dog_id)

class HistoryResponse(BaseModel):
    dogs: list[DogInfo]
    days: list[DaySummary]

DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

@router.get("/history/", response_model=HistoryResponse)
def get_history(days: int = 7, db: Session = Depends(get_db)):
    today = date.today()
    start = today - timedelta(days=days - 1)
    start_dt = datetime.combine(start, datetime.min.time())

    dogs = db.query(models.Dog).filter(models.Dog.active == True).order_by(models.Dog.name.desc()).all()

    rows = (
        db.query(
            func.strftime('%Y-%m-%d', models.PeePooEvent.timestamp).label('day'),
            models.PeePooEvent.dog_id,
            models.PeePooEvent.type,
            func.count().label('cnt'),
        )
        .filter(models.PeePooEvent.timestamp >= start_dt)
        .group_by('day', models.PeePooEvent.dog_id, models.PeePooEvent.type)
        .all()
    )

    lookup: dict[str, dict[int, dict[str, int]]] = {}
    for row in rows:
        lookup.setdefault(row.day, {}).setdefault(row.dog_id, {'pee': 0, 'poo': 0})[row.type] = row.cnt

    result_days = []
    for i in range(days):
        d = start + timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        day_counts = {
            str(dog.id): DayCount(
                pee=lookup.get(ds, {}).get(dog.id, {}).get('pee', 0),
                poo=lookup.get(ds, {}).get(dog.id, {}).get('poo', 0),
            )
            for dog in dogs
        }
        result_days.append(DaySummary(date=ds, label=DAY_LABELS[d.weekday()], counts=day_counts))

    return HistoryResponse(
        dogs=[DogInfo(id=d.id, name=d.name, track_pee=d.track_pee) for d in dogs],
        days=result_days,
    )
