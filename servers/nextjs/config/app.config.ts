/**
 * Application Configuration
 *
 * Set RESTRICT_TO_PRESENTATION_ONLY to true to restrict access to only the /presentation route.
 * All other routes will show a "Page Not Found" message.
 *
 * Change this value and rebuild to enable/disable the restriction.
 */

export const APP_CONFIG = {
  /**
   * When true: Only /presentation route is accessible, all other routes show NotFound
   * When false: All routes are accessible (default behavior)
   */
  RESTRICT_TO_PRESENTATION_ONLY: true,
} as const;
