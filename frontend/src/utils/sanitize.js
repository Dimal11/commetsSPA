import DOMPurify from 'dompurify'
export function sanitize(html) {
  return DOMPurify.sanitize(html ?? '', {
    ALLOWED_TAGS: ['a','code','i','strong'],
    ALLOWED_ATTR: ['href','title']
  })
}
