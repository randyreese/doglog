import Dexie from 'dexie'

export const db = new Dexie('doglog')

db.version(1).stores({
  dogs: 'id, name, active',
  events: 'id, dog_id, type, timestamp',
  eventQueue: '++id, dog_id, created_at',
  meta: 'key',
})

db.version(2).stores({
  dogs: 'id, name, active',
  events: 'id, dog_id, type, timestamp',
  eventQueue: '++id, dog_id, created_at',
  meta: 'key',
  healthEvents: 'id, dog_id, type, timestamp',
  healthQueue: '++id, dog_id, created_at',
})

db.version(3).stores({
  dogs: 'id, name, active',
  events: 'id, dog_id, type, timestamp',
  eventQueue: '++id, dog_id, created_at',
  meta: 'key',
  healthEvents: 'id, dog_id, type, timestamp',
  healthQueue: '++id, dog_id, created_at',
  mealLogs: '[dog_id+slot+meal_date], dog_id, meal_date',
  mealQueue: '++id, dog_id, meal_date',
})

db.version(4).stores({
  dogs: 'id, name, active',
  events: 'id, dog_id, type, timestamp',
  eventQueue: '++id, dog_id, created_at',
  meta: 'key',
  healthEvents: 'id, dog_id, type, timestamp',
  healthQueue: '++id, dog_id, created_at',
  mealLogs: '[dog_id+slot+meal_date], dog_id, meal_date',
  mealQueue: '++id, dog_id, meal_date',
  medicationLogs: '[dog_id+medication_id+log_date], dog_id, log_date',
  medicationQueue: '++id, dog_id, log_date',
})
