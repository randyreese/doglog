from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, LargeBinary, String, UniqueConstraint, func
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

    __table_args__ = (UniqueConstraint('dog_id', 'type', 'timestamp', name='uq_pee_poo_event'),)


class OtherEvent(Base):
    __tablename__ = "other_events"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    type = Column(String, nullable=False)  # 'vomit'|'diarrhea'|'grass_eating'|'stomach_gurgles'|'dry_heaves'|'other'
    photo = Column(LargeBinary, nullable=True)
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
    effective_date = Column(Date, nullable=False)


class MealConfigItem(Base):
    __tablename__ = "meal_config_items"
    id = Column(Integer, primary_key=True, index=True)
    meal_config_id = Column(Integer, nullable=False)
    food_name = Column(String, nullable=False)
    amount = Column(String, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)


class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


class MedicationDose(Base):
    __tablename__ = "medication_doses"
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    amount = Column(String, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=True)  # NULL = All
    date = Column(Date, nullable=False)
    event_type = Column(String, nullable=False)  # Life|Travel|Vet|Train|Experience
    notes1 = Column(String, nullable=True)
    notes2 = Column(String, nullable=True)
    weight_lbs = Column(Float, nullable=True)


class DryFood(Base):
    __tablename__ = "dry_food"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=True)
    product = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=True)


class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, nullable=False)
    slot = Column(String, nullable=False)       # key from meal_slots.ini
    meal_date = Column(Date, nullable=False)
    percent_consumed = Column(Integer, nullable=True)  # null=not logged, 0=skipped, 0-100
    notes = Column(String, nullable=True)
    ingredients = Column(String, nullable=True)  # JSON: {"kibble": true, "wet_food": false}

    __table_args__ = (UniqueConstraint('dog_id', 'slot', 'meal_date', name='uq_meal_log'),)
