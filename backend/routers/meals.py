from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional, List
import configparser
import json
from pathlib import Path
import models
from database import get_db

router = APIRouter()

_SLOTS_PATH = Path(__file__).parent.parent / 'meal_slots.ini'
_INGREDIENTS_PATH = Path(__file__).parent.parent / 'meal_ingredients.ini'


def _load_ini(path: Path) -> dict:
    config = configparser.ConfigParser()
    config.read(path)
    section = next(iter(config.sections()), None)
    return dict(config[section]) if section else {}


def _save_ini(path: Path, data: dict):
    section = 'slots' if path == _SLOTS_PATH else 'ingredients'
    config = configparser.ConfigParser()
    config[section] = data
    with open(path, 'w') as f:
        config.write(f)


class IniItemIn(BaseModel):
    label: str


@router.get("/meal-slots")
def get_meal_slots():
    return [{"value": k, "label": v} for k, v in _load_ini(_SLOTS_PATH).items()]


@router.post("/meal-slots")
def add_meal_slot(body: IniItemIn):
    label = body.label.strip()
    if not label:
        raise HTTPException(400, "label required")
    items = _load_ini(_SLOTS_PATH)
    key = label.lower().replace(" ", "_")
    if key in items:
        raise HTTPException(409, "slot already exists")
    items[key] = label
    _save_ini(_SLOTS_PATH, items)
    return {"value": key, "label": label}


@router.delete("/meal-slots/{key}")
def delete_meal_slot(key: str):
    items = _load_ini(_SLOTS_PATH)
    if key not in items:
        raise HTTPException(404, "slot not found")
    del items[key]
    _save_ini(_SLOTS_PATH, items)
    return {"ok": True}


@router.patch("/meal-slots/{key}")
def edit_meal_slot(key: str, body: IniItemIn):
    items = _load_ini(_SLOTS_PATH)
    if key not in items:
        raise HTTPException(404, "slot not found")
    items[key] = body.label.strip()
    _save_ini(_SLOTS_PATH, items)
    return {"value": key, "label": items[key]}


@router.put("/meal-slots")
def reorder_meal_slots(ordered: List[dict]):
    new_dict = {item["value"]: item["label"] for item in ordered}
    _save_ini(_SLOTS_PATH, new_dict)
    return [{"value": k, "label": v} for k, v in new_dict.items()]


@router.get("/meal-ingredients")
def get_meal_ingredients():
    return [{"value": k, "label": v} for k, v in _load_ini(_INGREDIENTS_PATH).items()]


@router.post("/meal-ingredients")
def add_meal_ingredient(body: IniItemIn):
    label = body.label.strip()
    if not label:
        raise HTTPException(400, "label required")
    items = _load_ini(_INGREDIENTS_PATH)
    key = label.lower().replace(" ", "_")
    if key in items:
        raise HTTPException(409, "ingredient already exists")
    items[key] = label
    _save_ini(_INGREDIENTS_PATH, items)
    return {"value": key, "label": label}


@router.delete("/meal-ingredients/{key}")
def delete_meal_ingredient(key: str):
    items = _load_ini(_INGREDIENTS_PATH)
    if key not in items:
        raise HTTPException(404, "ingredient not found")
    del items[key]
    _save_ini(_INGREDIENTS_PATH, items)
    return {"ok": True}


@router.patch("/meal-ingredients/{key}")
def edit_meal_ingredient(key: str, body: IniItemIn):
    items = _load_ini(_INGREDIENTS_PATH)
    if key not in items:
        raise HTTPException(404, "ingredient not found")
    items[key] = body.label.strip()
    _save_ini(_INGREDIENTS_PATH, items)
    return {"value": key, "label": items[key]}


@router.put("/meal-ingredients")
def reorder_meal_ingredients(ordered: List[dict]):
    new_dict = {item["value"]: item["label"] for item in ordered}
    _save_ini(_INGREDIENTS_PATH, new_dict)
    return [{"value": k, "label": v} for k, v in new_dict.items()]


class MealLogIn(BaseModel):
    dog_id: int
    slot: str
    meal_date: date
    percent_consumed: Optional[int] = None
    notes: Optional[str] = None
    ingredients: Optional[dict] = None  # {"kibble": True, "wet_food": False}


class MealLogOut(BaseModel):
    id: int
    dog_id: int
    slot: str
    meal_date: date
    percent_consumed: Optional[int]
    notes: Optional[str]
    ingredients: Optional[dict]

    model_config = {"from_attributes": True}


def _to_out(log) -> MealLogOut:
    return MealLogOut(
        id=log.id,
        dog_id=log.dog_id,
        slot=log.slot,
        meal_date=log.meal_date,
        percent_consumed=log.percent_consumed,
        notes=log.notes,
        ingredients=json.loads(log.ingredients) if log.ingredients else None,
    )


@router.get("/meal-logs/", response_model=list[MealLogOut])
def list_meal_logs(meal_date: date = Query(...), db: Session = Depends(get_db)):
    return [
        _to_out(log)
        for log in db.query(models.MealLog)
        .filter(models.MealLog.meal_date == meal_date)
        .all()
    ]


@router.get("/meal-logs/range/", response_model=list[MealLogOut])
def list_meal_logs_range(
    dog_id: int = Query(...),
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    since = date.today() - timedelta(days=days - 1)
    return [
        _to_out(log)
        for log in db.query(models.MealLog)
        .filter(models.MealLog.dog_id == dog_id, models.MealLog.meal_date >= since)
        .order_by(models.MealLog.meal_date.desc())
        .all()
    ]


@router.post("/meal-logs/", response_model=MealLogOut)
def upsert_meal_log(body: MealLogIn, db: Session = Depends(get_db)):
    ingredients_json = json.dumps(body.ingredients) if body.ingredients is not None else None
    existing = (
        db.query(models.MealLog)
        .filter_by(dog_id=body.dog_id, slot=body.slot, meal_date=body.meal_date)
        .first()
    )
    if existing:
        existing.percent_consumed = body.percent_consumed
        existing.notes = body.notes
        existing.ingredients = ingredients_json
        db.commit()
        db.refresh(existing)
        return _to_out(existing)
    log = models.MealLog(
        dog_id=body.dog_id,
        slot=body.slot,
        meal_date=body.meal_date,
        percent_consumed=body.percent_consumed,
        notes=body.notes,
        ingredients=ingredients_json,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _to_out(log)
