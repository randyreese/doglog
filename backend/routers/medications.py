from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date as Date
from typing import Optional, List
import models
from database import get_db

router = APIRouter()


class MedicationDoseIn(BaseModel):
    label: str
    amount: Optional[str] = None
    sort_order: int = 0


class MedicationIn(BaseModel):
    dog_id: int
    name: str
    start_date: Optional[Date] = None
    end_date: Optional[Date] = None
    doses: List[MedicationDoseIn]


class MedicationPatch(BaseModel):
    start_date: Optional[Date] = None
    end_date: Optional[Date] = None
    doses: Optional[List[MedicationDoseIn]] = None


class MedicationDoseOut(BaseModel):
    id: int
    label: str
    amount: Optional[str]
    sort_order: int

    model_config = {"from_attributes": True}


class MedicationOut(BaseModel):
    id: int
    dog_id: int
    name: str
    start_date: Optional[Date]
    end_date: Optional[Date]
    doses: List[MedicationDoseOut]

    model_config = {"from_attributes": True}


def _med_out(med: models.Medication, db: Session) -> MedicationOut:
    doses = (
        db.query(models.MedicationDose)
        .filter(models.MedicationDose.medication_id == med.id)
        .order_by(models.MedicationDose.sort_order)
        .all()
    )
    return MedicationOut(
        id=med.id,
        dog_id=med.dog_id,
        name=med.name,
        start_date=med.start_date,
        end_date=med.end_date,
        doses=[MedicationDoseOut.model_validate(d) for d in doses],
    )


@router.get("/medications/", response_model=List[MedicationOut])
def get_medications(dog_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Medication)
    if dog_id is not None:
        q = q.filter(models.Medication.dog_id == dog_id)
    meds = q.order_by(models.Medication.dog_id, models.Medication.name).all()
    return [_med_out(med, db) for med in meds]


@router.post("/medications/", response_model=MedicationOut)
def create_medication(body: MedicationIn, db: Session = Depends(get_db)):
    med = models.Medication(
        dog_id=body.dog_id,
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    db.add(med)
    db.flush()
    for dose in body.doses:
        db.add(models.MedicationDose(
            medication_id=med.id,
            label=dose.label,
            amount=dose.amount,
            sort_order=dose.sort_order,
        ))
    db.commit()
    db.refresh(med)
    return _med_out(med, db)


@router.patch("/medications/{med_id}", response_model=MedicationOut)
def update_medication(med_id: int, body: MedicationPatch, db: Session = Depends(get_db)):
    med = db.query(models.Medication).filter(models.Medication.id == med_id).first()
    if not med:
        raise HTTPException(404, "medication not found")
    data = body.model_dump(exclude_unset=True)
    doses = data.pop('doses', None)
    for field, value in data.items():
        setattr(med, field, value)
    if doses is not None:
        db.query(models.MedicationDose).filter(
            models.MedicationDose.medication_id == med_id
        ).delete()
        for dose in doses:
            db.add(models.MedicationDose(
                medication_id=med_id,
                label=dose['label'],
                amount=dose.get('amount'),
                sort_order=dose.get('sort_order', 0),
            ))
    db.commit()
    db.refresh(med)
    return _med_out(med, db)


@router.delete("/medications/{med_id}")
def delete_medication(med_id: int, db: Session = Depends(get_db)):
    med = db.query(models.Medication).filter(models.Medication.id == med_id).first()
    if not med:
        raise HTTPException(404, "medication not found")
    db.query(models.MedicationDose).filter(
        models.MedicationDose.medication_id == med_id
    ).delete()
    db.delete(med)
    db.commit()
    return {"ok": True}
