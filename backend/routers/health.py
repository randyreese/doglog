from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import base64
import models
from database import get_db

router = APIRouter()

VALID_TYPES = {'vomit', 'diarrhea', 'grass_eating', 'stomach_gurgles', 'dry_heaves', 'other'}


class HealthEventIn(BaseModel):
    dog_id: int
    type: str
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    photo: Optional[str] = None  # base64-encoded


class HealthEventPatch(BaseModel):
    notes: Optional[str] = None
    photo: Optional[str] = None  # base64-encoded


class HealthEventOut(BaseModel):
    id: int
    dog_id: int
    type: str
    timestamp: datetime
    notes: Optional[str]
    photo: Optional[str]  # base64-encoded or None

    model_config = {"from_attributes": True}


def _to_out(event) -> HealthEventOut:
    return HealthEventOut(
        id=event.id,
        dog_id=event.dog_id,
        type=event.type,
        timestamp=event.timestamp,
        notes=event.notes,
        photo=base64.b64encode(event.photo).decode('utf-8') if event.photo else None,
    )


@router.post("/health-events/", response_model=HealthEventOut, status_code=201)
def log_health_event(body: HealthEventIn, db: Session = Depends(get_db)):
    if body.type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid type: {body.type}")
    dog = db.query(models.Dog).filter(models.Dog.id == body.dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    event = models.OtherEvent(
        dog_id=body.dog_id,
        type=body.type,
        timestamp=body.timestamp or datetime.now(),
        notes=body.notes,
        photo=base64.b64decode(body.photo) if body.photo else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _to_out(event)


@router.get("/health-events/", response_model=list[HealthEventOut])
def list_health_events(
    dog_id: Optional[int] = Query(None),
    since: Optional[datetime] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    q = db.query(models.OtherEvent)
    if dog_id is not None:
        q = q.filter(models.OtherEvent.dog_id == dog_id)
    if since is not None:
        q = q.filter(models.OtherEvent.timestamp >= since)
    return [_to_out(e) for e in q.order_by(models.OtherEvent.timestamp.desc()).limit(limit).all()]


@router.patch("/health-events/{event_id}", response_model=HealthEventOut)
def patch_health_event(event_id: int, body: HealthEventPatch, db: Session = Depends(get_db)):
    event = db.query(models.OtherEvent).filter(models.OtherEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if body.notes is not None:
        event.notes = body.notes
    if body.photo is not None:
        event.photo = base64.b64decode(body.photo)
    db.commit()
    db.refresh(event)
    return _to_out(event)


@router.delete("/health-events/{event_id}", status_code=204)
def delete_health_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.OtherEvent).filter(models.OtherEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
