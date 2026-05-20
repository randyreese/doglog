from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, func
from database import Base


class Dog(Base):
    __tablename__ = "dogs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    birthdate = Column(Date, nullable=True)
    breed = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    track_pee = Column(Boolean, default=True, nullable=False)


class PeePooEvent(Base):
    __tablename__ = "pee_poo_events"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    type = Column(String, nullable=False)  # 'pee' | 'poo'


class OtherEvent(Base):
    __tablename__ = "other_events"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    type = Column(String, nullable=False)  # 'vomit' | 'diarrhea' | 'other'
    photo_path = Column(String, nullable=True)
    notes = Column(String, nullable=True)


class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    meal_slot = Column(String, nullable=False)  # 'am' | 'pm'
    consumed_pct = Column(Integer, nullable=False)  # 0 | 25 | 50 | 75 | 100


class MealConfig(Base):
    __tablename__ = "meal_configs"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    meal_slot = Column(String, nullable=False)
    food_name = Column(String, nullable=False)
    amount = Column(String, nullable=True)
    effective_date = Column(Date, nullable=False)


class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)  # 'vet_visit' | 'weight' | 'trip' | 'other'
    notes = Column(String, nullable=True)


class DryFood(Base):
    __tablename__ = "dry_food"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=True)
    product = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=True)
