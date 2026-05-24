from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, Literal
import models
from database import get_db

router = APIRouter()


class EventIn(BaseModel):
    dog_id: int
    type: Literal['pee', 'poo']
    timestamp: Optional[datetime] = None


class EventOut(BaseModel):
    id: int
    dog_id: int
    type: str
    timestamp: datetime

    model_config = {"from_attributes": True}


@router.post("/events/", response_model=EventOut, status_code=201)
def log_event(body: EventIn, db: Session = Depends(get_db)):
    dog = db.query(models.Dog).filter(models.Dog.id == body.dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    ts = body.timestamp or datetime.now()
    event = models.PeePooEvent(dog_id=body.dog_id, type=body.type, timestamp=ts)
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
        return event
    except IntegrityError:
        db.rollback()
        return db.query(models.PeePooEvent).filter(
            models.PeePooEvent.dog_id == body.dog_id,
            models.PeePooEvent.type == body.type,
            models.PeePooEvent.timestamp == ts,
        ).first()


@router.get("/events/", response_model=list[EventOut])
def list_events(
    dog_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    q = db.query(models.PeePooEvent)
    if dog_id is not None:
        q = q.filter(models.PeePooEvent.dog_id == dog_id)
    if type is not None:
        q = q.filter(models.PeePooEvent.type == type)
    if since is not None:
        q = q.filter(models.PeePooEvent.timestamp >= since)
    return q.order_by(models.PeePooEvent.timestamp.desc()).limit(limit).all()


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.PeePooEvent).filter(models.PeePooEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
