const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export async function uploadAttachmentREST(commentId, file) {
  if (!commentId) throw new Error('commentId is required')
  if (!file) return null

  const fd = new FormData()
  fd.append('commentId', String(commentId))
  fd.append('file', file)

  const res = await fetch(`${API_BASE}/api/attachments/upload/`, {
    method: 'POST',
    body: fd,
    credentials: 'include',
  })

  let data = null
  try { data = await res.json() } catch (_) {}

  if (!res.ok) {
    const msg = (data && (data.error || data.detail)) || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}