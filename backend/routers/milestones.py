from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
import configparser
from pathlib import Path
import models
from database import get_db

router = APIRouter()

_EVENT_TYPES_PATH = Path(__file__).parent.parent / 'milestone_event_types.ini'
_MED_NAMES_PATH = Path(__file__).parent.parent / 'medication_names.ini'


def _load_ini(path: Path) -> dict:
    config = configparser.ConfigParser()
    config.read(path)
    section = next(iter(config.sections()), None)
    return dict(config[section]) if section else {}


def _save_ini(path: Path, data: dict, section: str = 'types'):
    config = configparser.ConfigParser()
    config[section] = data
    with open(path, 'w') as f:
        config.write(f)


# ── Milestone event types config ─────────────────────────────────────────────

@router.get("/milestone-event-types")
def get_event_types():
    return [{"value": k, "label": v} for k, v in _load_ini(_EVENT_TYPES_PATH).items()]


class EventTypeIn(BaseModel):
    label: str


@router.post("/milestone-event-types")
def add_event_type(body: EventTypeIn):
    label = body.label.strip()
    if not label:
        raise HTTPException(400, "label required")
    types = _load_ini(_EVENT_TYPES_PATH)
    key = label.lower().replace(" ", "_")
    if key in types:
        raise HTTPException(409, "type already exists")
    types[key] = label
    _save_ini(_EVENT_TYPES_PATH, types)
    return {"value": key, "label": label}


@router.delete("/milestone-event-types/{key}")
def delete_event_type(key: str):
    types = _load_ini(_EVENT_TYPES_PATH)
    if key not in types:
        raise HTTPException(404, "type not found")
    del types[key]
    _save_ini(_EVENT_TYPES_PATH, types)
    return {"ok": True}


@router.patch("/milestone-event-types/{key}")
def edit_event_type(key: str, body: EventTypeIn):
    types = _load_ini(_EVENT_TYPES_PATH)
    if key not in types:
        raise HTTPException(404, "type not found")
    types[key] = body.label.strip()
    _save_ini(_EVENT_TYPES_PATH, types)
    return {"value": key, "label": types[key]}


@router.put("/milestone-event-types")
def reorder_event_types(items: List[dict]):
    new_dict = {item["value"]: item["label"] for item in items}
    _save_ini(_EVENT_TYPES_PATH, new_dict)
    return [{"value": k, "label": v} for k, v in new_dict.items()]


# ── Medication names config ───────────────────────────────────────────────────

@router.get("/medication-names")
def get_medication_names():
    return [{"value": k, "label": v} for k, v in _load_ini(_MED_NAMES_PATH).items()]


class MedNameIn(BaseModel):
    label: str


@router.post("/medication-names")
def add_medication_name(body: MedNameIn):
    label = body.label.strip()
    if not label:
        raise HTTPException(400, "label required")
    names = _load_ini(_MED_NAMES_PATH)
    key = label.lower().replace(" ", "_")
    if key in names:
        raise HTTPException(409, "name already exists")
    names[key] = label
    _save_ini(_MED_NAMES_PATH, names, section='names')
    return {"value": key, "label": label}


@router.delete("/medication-names/{key}")
def delete_medication_name(key: str):
    names = _load_ini(_MED_NAMES_PATH)
    if key not in names:
        raise HTTPException(404, "name not found")
    del names[key]
    _save_ini(_MED_NAMES_PATH, names, section='names')
    return {"ok": True}


@router.patch("/medication-names/{key}")
def edit_medication_name(key: str, body: MedNameIn):
    names = _load_ini(_MED_NAMES_PATH)
    if key not in names:
        raise HTTPException(404, "name not found")
    names[key] = body.label.strip()
    _save_ini(_MED_NAMES_PATH, names, section='names')
    return {"value": key, "label": names[key]}


@router.put("/medication-names")
def reorder_medication_names(items: List[dict]):
    new_dict = {item["value"]: item["label"] for item in items}
    _save_ini(_MED_NAMES_PATH, new_dict, section='names')
    return [{"value": k, "label": v} for k, v in new_dict.items()]


# ── Milestones CRUD ───────────────────────────────────────────────────────────

class MilestoneIn(BaseModel):
    dog_id: Optional[int] = None
    date: date
    event_type: str
    notes1: Optional[str] = None
    notes2: Optional[str] = None
    weight_lbs: Optional[float] = None


class MilestonePatch(BaseModel):
    dog_id: Optional[int] = None
    date: Optional[date] = None
    event_type: Optional[str] = None
    notes1: Optional[str] = None
    notes2: Optional[str] = None
    weight_lbs: Optional[float] = None


class MilestoneOut(BaseModel):
    id: int
    dog_id: Optional[int]
    date: date
    event_type: str
    notes1: Optional[str]
    notes2: Optional[str]
    weight_lbs: Optional[float]

    model_config = {"from_attributes": True}


@router.get("/milestones/", response_model=List[MilestoneOut])
def get_milestones(
    dog_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Milestone)
    if dog_id is not None:
        q = q.filter(
            (models.Milestone.dog_id == dog_id) | (models.Milestone.dog_id.is_(None))
        )
    if event_type:
        q = q.filter(models.Milestone.event_type == event_type)
    return q.order_by(models.Milestone.date.desc()).all()


@router.post("/milestones/", response_model=MilestoneOut)
def create_milestone(body: MilestoneIn, db: Session = Depends(get_db)):
    m = models.Milestone(**body.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.patch("/milestones/{id}", response_model=MilestoneOut)
def update_milestone(id: int, body: MilestonePatch, db: Session = Depends(get_db)):
    m = db.query(models.Milestone).filter(models.Milestone.id == id).first()
    if not m:
        raise HTTPException(404, "milestone not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/milestones/{id}")
def delete_milestone(id: int, db: Session = Depends(get_db)):
    m = db.query(models.Milestone).filter(models.Milestone.id == id).first()
    if not m:
        raise HTTPException(404, "milestone not found")
    db.delete(m)
    db.commit()
    return {"ok": True}
