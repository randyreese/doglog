import Dexie from 'dexie'

export const db = new Dexie('doglog')

db.version(1).stores({
  dogs: 'id, name, active',
  events: 'id, dog_id, type, timestamp',
  eventQueue: '++id, dog_id, created_at',
  meta: 'key',
})
