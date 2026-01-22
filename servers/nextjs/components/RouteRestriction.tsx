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

  // Allow specific routes needed for functionality
  const allowedRoutes = [
    '/presentation',
    '/api/download',
    '/pdf-maker',
    '/api/export-as-pdf',
    '/api/presentation_to_pptx_model',
  ]

  // Check if current path starts with any allowed route
  if (allowedRoutes.some(route => pathname.startsWith(route))) {
    return <>{children}</>
  }

  // For all other routes, show not found
  return <NotFound />
}
