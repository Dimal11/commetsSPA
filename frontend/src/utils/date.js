export function formatDate(iso) {
  try {
    return new Intl.DateTimeFormat('ru-RU', {
      year:'numeric', month:'2-digit', day:'2-digit',
      hour:'2-digit', minute:'2-digit'
    }).format(new Date(iso))
  } catch { return iso || '' }
}
