import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from './api'
import { useSyncContext } from './SyncContext'

const ConfigContext = createContext(null)

function loadCached(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback }
  catch { return fallback }
}

export function ConfigProvider({ children }) {
  const { syncVersion } = useSyncContext()
  const [dogs, setDogs] = useState(() => loadCached('cfg_dogs', []))
  const [healthTypes, setHealthTypes] = useState(() => loadCached('cfg_health_types', []))
  const [mealSlots, setMealSlots] = useState(() => loadCached('cfg_meal_slots', []))
  const [mealIngredients, setMealIngredients] = useState(() => loadCached('cfg_meal_ingredients', []))
  // mealConfigs: {`${dogId}:${slotKey}`: [{value: food_name, label: food_name}]}
  const [mealConfigs, setMealConfigs] = useState(() => loadCached('cfg_meal_configs', {}))
  // medications: active only [{id, dog_id, name, start_date, end_date, doses}]
  const [medications, setMedications] = useState(() => loadCached('cfg_medications', []))
  const [milestoneEventTypes, setMilestoneEventTypes] = useState(() => loadCached('cfg_milestone_event_types', []))

  const load = useCallback(async () => {
    try {
      const [dogsData, typesData, slotsData, ingredientsData] = await Promise.all([
        api.get('/dogs/'),
        api.get('/health-types'),
        api.get('/meal-slots'),
        api.get('/meal-ingredients'),
      ])
      const sorted = [...dogsData].sort((a, b) => b.name.localeCompare(a.name))
      setDogs(sorted)
      setHealthTypes(typesData)
      setMealSlots(slotsData)
      setMealIngredients(ingredientsData)
      localStorage.setItem('cfg_dogs', JSON.stringify(sorted))
      localStorage.setItem('cfg_health_types', JSON.stringify(typesData))
      localStorage.setItem('cfg_meal_slots', JSON.stringify(slotsData))
      localStorage.setItem('cfg_meal_ingredients', JSON.stringify(ingredientsData))
    } catch { /* offline — use cached */ }

    // Meal configs fetched independently so a failure doesn't block other config
    try {
      const configsData = await api.get('/meal-configs/')
      const cfgMap = {}
      for (const cfg of configsData) {
        const key = `${cfg.dog_id}:${cfg.meal_slot}`
        if (!cfgMap[key]) {
          cfgMap[key] = cfg.items.map(it => ({ value: it.food_name, label: it.food_name }))
        }
      }
      setMealConfigs(cfgMap)
      localStorage.setItem('cfg_meal_configs', JSON.stringify(cfgMap))
    } catch(e) {
      console.error('meal-configs load failed:', e.message)
    }

    try {
      const milestoneTypesData = await api.get('/milestone-event-types')
      setMilestoneEventTypes(milestoneTypesData)
      localStorage.setItem('cfg_milestone_event_types', JSON.stringify(milestoneTypesData))
    } catch(e) {
      console.error('milestone-event-types load failed:', e.message)
    }

    // Active medications (end_date null or in future)
    try {
      const medsData = await api.get('/medications/')
      const today = new Date().toISOString().slice(0, 10)
      const active = medsData.filter(m => !m.end_date || m.end_date >= today)
      setMedications(active)
      localStorage.setItem('cfg_medications', JSON.stringify(active))
    } catch(e) {
      console.error('medications load failed:', e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => { if (syncVersion > 0) load() }, [syncVersion, load])

  const dogMap = Object.fromEntries(dogs.map(d => [d.id, d.name]))

  return (
    <ConfigContext.Provider value={{ dogs, healthTypes, mealSlots, mealIngredients, mealConfigs, medications, milestoneEventTypes, dogMap }}>
      {children}
    </ConfigContext.Provider>
  )
}

export function useConfig() {
  return useContext(ConfigContext)
}
