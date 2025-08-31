// src/paths.js
// Base URLs for API and file storage. Override in .env as needed.
export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/,'')
export const FILES_BASE = (import.meta.env.VITE_FILES_BASE_URL ?? API_BASE).replace(/\/$/,'')

/**
 * Build an absolute URL for files/images that may come as relative paths.
 * - http(s):// and protocol-relative URLs are returned as-is
 * - data: URLs returned as-is
 * - '/media/...': prefix FILES_BASE
 * - 'media/...': prefix FILES_BASE + '/'
 */
export function absUrl(u) {
  if (!u) return ''
  if (typeof u !== 'string') u = String(u)
  if (/^(?:https?:)?\/\//i.test(u) || u.startsWith('data:')) return u
  if (u.startsWith('/')) return FILES_BASE + u
  return FILES_BASE + '/' + u
}
