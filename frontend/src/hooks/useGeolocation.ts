import { useState, useEffect } from 'react'

interface GeolocationState {
  city: string
  loading: boolean
  error: string | null
  coords: { lat: number; lng: number } | null
}

export function useGeolocation(): GeolocationState {
  const [state, setState] = useState<GeolocationState>({
    city: '',
    loading: true,
    error: null,
    coords: null,
  })

  useEffect(() => {
    if (!navigator.geolocation) {
      setState(s => ({ ...s, loading: false, error: 'Geolocation not supported' }))
      return
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&accept-language=en`,
            { headers: { 'User-Agent': 'InterviewCoach/1.0' } }
          )
          const data = await res.json()
          const address = data.address || {}
          const city = address.city || address.town || address.village || address.county || ''
          const stateRegion = address.state || ''
          const locationStr = city + (stateRegion ? `, ${stateRegion}` : '')
          setState({
            city: locationStr || 'Unknown location',
            loading: false,
            error: null,
            coords: { lat: latitude, lng: longitude },
          })
        } catch {
          setState(s => ({
            ...s,
            loading: false,
            city: `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`,
            coords: { lat: latitude, lng: longitude },
          }))
        }
      },
      (err) => {
        setState(s => ({ ...s, loading: false, error: err.message }))
      },
      { enableHighAccuracy: false, timeout: 10000 }
    )
  }, [])

  return state
}
