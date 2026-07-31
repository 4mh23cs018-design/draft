import { useState, useEffect } from 'react'
import { getHealth, HealthStatus } from '../services/api'

export function useHealth() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        const h = await getHealth()
        setHealth(h)
        setOnline(h.status === 'ok')
      } catch {
        setOnline(false)
      }
    }
    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [])

  return { health, online }
}
