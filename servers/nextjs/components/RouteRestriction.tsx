'use client'

import { usePathname } from 'next/navigation'
import { APP_CONFIG } from '@/config/app.config'
import NotFound from '@/app/not-found'

interface RouteRestrictionProps {
  children: React.ReactNode
}

export default function RouteRestriction({ children }: RouteRestrictionProps) {
  const pathname = usePathname()

  // If restriction is not enabled, render children normally
  if (!APP_CONFIG.RESTRICT_TO_PRESENTATION_ONLY) {
    return <>{children}</>
  }

  // Allow /presentation route
  if (pathname.startsWith('/presentation')) {
    return <>{children}</>
  }

  // For all other routes, show not found
  return <NotFound />
}
