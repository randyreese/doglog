from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, date
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
