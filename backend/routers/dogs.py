from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date as Date
from typing import Optional
import models
from database import get_db

router = APIRouter()


class DogIn(BaseModel):
    name: str
    birthdate: Optional[Date] = None
    breed: Optional[str] = None
    active: bool = True
    track_pee: bool = True


class DogOut(BaseModel):
    id: int
    name: str
    birthdate: Optional[Date]
    breed: Optional[str]
    active: bool
    track_pee: bool

    model_config = {"from_attributes": True}


@router.get("/dogs/", response_model=list[DogOut])
def list_dogs(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Dog)
    if active_only:
        q = q.filter(models.Dog.active == True)
    return q.order_by(models.Dog.name).all()


@router.post("/dogs/", response_model=DogOut, status_code=201)
def create_dog(body: DogIn, db: Session = Depends(get_db)):
    dog = models.Dog(**body.model_dump())
    db.add(dog)
    db.commit()
    db.refresh(dog)
    return dog


@router.get("/dogs/{dog_id}", response_model=DogOut)
def get_dog(dog_id: int, db: Session = Depends(get_db)):
    dog = db.query(models.Dog).filter(models.Dog.id == dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return dog


@router.patch("/dogs/{dog_id}", response_model=DogOut)
def update_dog(dog_id: int, body: DogIn, db: Session = Depends(get_db)):
    dog = db.query(models.Dog).filter(models.Dog.id == dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(dog, k, v)
    db.commit()
    db.refresh(dog)
    return dog
