from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import base64
import configparser
from pathlib import Path
import models
from database import get_db

router = APIRouter()

_INI_PATH = Path(__file__).parent.parent / 'health_types.ini'


def _read_ini() -> tuple[dict, dict]:
    """Returns (labels_dict, report_cols_dict)."""
    config = configparser.ConfigParser()
    config.read(_INI_PATH)
    labels = dict(config['types']) if 'types' in config else {}
    rcols = dict(config['report_columns']) if 'report_columns' in config else {}
    return labels, rcols


def _write_ini(labels: dict, rcols: dict):
    config = configparser.ConfigParser()
    config['types'] = labels
    config['report_columns'] = {k: v for k, v in rcols.items() if v}
    with open(_INI_PATH, 'w') as f:
        config.write(f)


@router.get("/health-types")
def get_health_types():
    labels, rcols = _read_ini()
    return [
        {"value": k, "label": v, "report_column": rcols.get(k, "")}
        for k, v in labels.items()
    ]


class HealthTypeIn(BaseModel):
    label: str
    report_column: Optional[str] = ""


@router.post("/health-types")
def add_health_type(body: HealthTypeIn):
    label = body.label.strip()
    if not label:
        raise HTTPException(400, "label required")
    labels, rcols = _read_ini()
    key = label.lower().replace(" ", "_")
    if key in labels:
        raise HTTPException(409, "type already exists")
    labels[key] = label
    if body.report_column:
        rcols[key] = body.report_column
    _write_ini(labels, rcols)
    return {"value": key, "label": label, "report_column": rcols.get(key, "")}


@router.delete("/health-types/{key}")
def delete_health_type(key: str):
    labels, rcols = _read_ini()
    if key not in labels:
        raise HTTPException(404, "type not found")
    del labels[key]
    rcols.pop(key, None)
    _write_ini(labels, rcols)
    return {"ok": True}


@router.patch("/health-types/{key}")
def edit_health_type(key: str, body: HealthTypeIn):
    labels, rcols = _read_ini()
    if key not in labels:
        raise HTTPException(404, "type not found")
    labels[key] = body.label.strip()
    if body.report_column:
        rcols[key] = body.report_column
    else:
        rcols.pop(key, None)
    _write_ini(labels, rcols)
    return {"value": key, "label": labels[key], "report_column": rcols.get(key, "")}


@router.put("/health-types")
def reorder_health_types(items: List[dict]):
    labels = {item["value"]: item["label"] for item in items}
    rcols = {item["value"]: item["report_column"] for item in items if item.get("report_column")}
    _write_ini(labels, rcols)
    labels2, rcols2 = _read_ini()
    return [
        {"value": k, "label": v, "report_column": rcols2.get(k, "")}
        for k, v in labels2.items()
    ]


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
    labels, _ = _read_ini()
    if body.type not in labels:
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
    until: Optional[datetime] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    q = db.query(models.OtherEvent)
    if dog_id is not None:
        q = q.filter(models.OtherEvent.dog_id == dog_id)
    if since is not None:
        q = q.filter(models.OtherEvent.timestamp >= since)
    if until is not None:
        q = q.filter(models.OtherEvent.timestamp <= until)
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
