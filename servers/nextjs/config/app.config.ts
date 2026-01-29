/**
 * Application Configuration
 *
 * Route restriction is now domain-based:
 * - On 'slides.tubeonai.com': Only /presentation route is accessible
 * - On other domains (localhost, etc.): All routes are accessible
 *
 * See RouteRestriction.tsx for implementation details.
 */

export const APP_CONFIG = {
  /**
   * The domain where route restriction is applied.
   * All domains except this one will have full access to all routes.
   */
  RESTRICTED_DOMAIN: 'slides.tubeonai.com',
} as const;
