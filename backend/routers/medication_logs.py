from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date as Date
from typing import Optional
import json
import models
from database import get_db

router = APIRouter()


class MedicationLogIn(BaseModel):
    dog_id: int
    medication_id: int
    log_date: Date
    doses_given: list[str]


class MedicationLogOut(BaseModel):
    id: int
    dog_id: int
    medication_id: int
    log_date: Date
    doses_given: list[str]

    model_config = {"from_attributes": True}


def _to_out(log) -> MedicationLogOut:
    return MedicationLogOut(
        id=log.id,
        dog_id=log.dog_id,
        medication_id=log.medication_id,
        log_date=log.log_date,
        doses_given=json.loads(log.doses_given),
    )


@router.get("/medication-logs/", response_model=list[MedicationLogOut])
def list_medication_logs(
    dog_id: int = Query(...),
    log_date: Date = Query(...),
    db: Session = Depends(get_db),
):
    return [
        _to_out(log)
        for log in db.query(models.MedicationLog)
        .filter_by(dog_id=dog_id, log_date=log_date)
        .all()
    ]


@router.get("/medication-logs/range/", response_model=list[MedicationLogOut])
def list_medication_logs_range(
    dog_id: int = Query(...),
    start_date: Date = Query(...),
    end_date: Date = Query(...),
    db: Session = Depends(get_db),
):
    return [
        _to_out(log)
        for log in db.query(models.MedicationLog)
        .filter(
            models.MedicationLog.dog_id == dog_id,
            models.MedicationLog.log_date >= start_date,
            models.MedicationLog.log_date <= end_date,
        )
        .all()
    ]


@router.post("/medication-logs/", response_model=MedicationLogOut)
def upsert_medication_log(body: MedicationLogIn, db: Session = Depends(get_db)):
    doses_json = json.dumps(body.doses_given)
    existing = (
        db.query(models.MedicationLog)
        .filter_by(dog_id=body.dog_id, medication_id=body.medication_id, log_date=body.log_date)
        .first()
    )
    if existing:
        existing.doses_given = doses_json
        db.commit()
        db.refresh(existing)
        return _to_out(existing)
    log = models.MedicationLog(
        dog_id=body.dog_id,
        medication_id=body.medication_id,
        log_date=body.log_date,
        doses_given=doses_json,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _to_out(log)
