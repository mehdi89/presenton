'use client'

import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { APP_CONFIG } from '@/config/app.config'
import NotFound from '@/app/not-found'

interface RouteRestrictionProps {
  children: React.ReactNode
}

export default function RouteRestriction({ children }: RouteRestrictionProps) {
  const pathname = usePathname()
  const [isRestricted, setIsRestricted] = useState<boolean | null>(null)

  useEffect(() => {
    // Check if the current domain should be restricted
    const hostname = window.location.hostname
    setIsRestricted(hostname === APP_CONFIG.RESTRICTED_DOMAIN)
  }, [])

  // During SSR or initial render, show children to avoid flash
  if (isRestricted === null) {
    return <>{children}</>
  }

  // If not on restricted domain, render children normally
  if (!isRestricted) {
    return <>{children}</>
  }

  // Allow specific routes needed for functionality on restricted domain
  const allowedRoutes = [
    '/presentation',
    '/api/download',
    '/pdf-maker',
    '/api/export-presentation',
    '/api/export-presentation-data',
  ]

  // Check if current path starts with any allowed route
  if (allowedRoutes.some(route => pathname.startsWith(route))) {
    return <>{children}</>
  }

  // For all other routes on restricted domain, show not found
  return <NotFound />
}
