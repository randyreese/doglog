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
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => { if (syncVersion > 0) load() }, [syncVersion, load])

  const dogMap = Object.fromEntries(dogs.map(d => [d.id, d.name]))

  return (
    <ConfigContext.Provider value={{ dogs, healthTypes, mealSlots, mealIngredients, dogMap }}>
      {children}
    </ConfigContext.Provider>
  )
}

export function useConfig() {
  return useContext(ConfigContext)
}
