from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date as Date
from typing import Optional, List
import models
from database import get_db

router = APIRouter()


class MealConfigItemIn(BaseModel):
    food_name: str
    amount: Optional[str] = None
    sort_order: int = 0


class MealConfigIn(BaseModel):
    dog_id: int
    meal_slot: str
    effective_date: Date
    items: List[MealConfigItemIn]


class MealConfigPatch(BaseModel):
    effective_date: Optional[Date] = None
    items: Optional[List[MealConfigItemIn]] = None


class MealConfigItemOut(BaseModel):
    id: int
    food_name: str
    amount: Optional[str]
    sort_order: int

    model_config = {"from_attributes": True}


class MealConfigOut(BaseModel):
    id: int
    dog_id: int
    meal_slot: str
    effective_date: Date
    items: List[MealConfigItemOut]

    model_config = {"from_attributes": True}


def _config_out(cfg: models.MealConfig, db: Session) -> MealConfigOut:
    items = (
        db.query(models.MealConfigItem)
        .filter(models.MealConfigItem.meal_config_id == cfg.id)
        .order_by(models.MealConfigItem.sort_order)
        .all()
    )
    return MealConfigOut(
        id=cfg.id,
        dog_id=cfg.dog_id,
        meal_slot=cfg.meal_slot,
        effective_date=cfg.effective_date,
        items=[MealConfigItemOut.model_validate(i) for i in items],
    )


@router.get("/meal-configs/", response_model=List[MealConfigOut])
def get_meal_configs(dog_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.MealConfig)
    if dog_id is not None:
        q = q.filter(models.MealConfig.dog_id == dog_id)
    configs = q.order_by(models.MealConfig.dog_id, models.MealConfig.meal_slot, models.MealConfig.effective_date.desc()).all()
    return [_config_out(cfg, db) for cfg in configs]


@router.post("/meal-configs/", response_model=MealConfigOut)
def create_meal_config(body: MealConfigIn, db: Session = Depends(get_db)):
    cfg = models.MealConfig(
        dog_id=body.dog_id,
        meal_slot=body.meal_slot,
        effective_date=body.effective_date,
    )
    db.add(cfg)
    db.flush()
    for item in body.items:
        db.add(models.MealConfigItem(
            meal_config_id=cfg.id,
            food_name=item.food_name,
            amount=item.amount,
            sort_order=item.sort_order,
        ))
    db.commit()
    db.refresh(cfg)
    return _config_out(cfg, db)


@router.patch("/meal-configs/{config_id}", response_model=MealConfigOut)
def update_meal_config(config_id: int, body: MealConfigPatch, db: Session = Depends(get_db)):
    cfg = db.query(models.MealConfig).filter(models.MealConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(404, "meal config not found")
    data = body.model_dump(exclude_unset=True)
    items = data.pop('items', None)
    for field, value in data.items():
        setattr(cfg, field, value)
    if items is not None:
        db.query(models.MealConfigItem).filter(
            models.MealConfigItem.meal_config_id == config_id
        ).delete()
        for item in items:
            db.add(models.MealConfigItem(
                meal_config_id=config_id,
                food_name=item['food_name'],
                amount=item.get('amount'),
                sort_order=item.get('sort_order', 0),
            ))
    db.commit()
    db.refresh(cfg)
    return _config_out(cfg, db)


@router.delete("/meal-configs/{config_id}")
def delete_meal_config(config_id: int, db: Session = Depends(get_db)):
    cfg = db.query(models.MealConfig).filter(models.MealConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(404, "meal config not found")
    db.query(models.MealConfigItem).filter(
        models.MealConfigItem.meal_config_id == config_id
    ).delete()
    db.delete(cfg)
    db.commit()
    return {"ok": True}
