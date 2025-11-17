const URL_REGEX = /(https?:\/\/[^\s]+)/gi
const URL_CHECK_REGEX = /^https?:\/\/[^\s]+$/i
const GIF_HINT_REGEX = /(tenor\.com|giphy\.com|\.gif($|\?))/i
const GIF_CLEANUP_REGEX = /[\u200B-\u200D\uFEFF]/g
const EMOJI_ONLY_REGEX = /^[\p{Extended_Pictographic}\u200d\s]+$/u

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function detectGifLinks(value = '') {
  if (!value) return []
  const candidates = value.split(/\s+/).filter(Boolean)
  const links = candidates
    .map((token) => token.trim().replace(GIF_CLEANUP_REGEX, ''))
    .filter((token) => URL_CHECK_REGEX.test(token) && GIF_HINT_REGEX.test(token))
  return [...new Set(links)]
}

export function stripGifLinks(value = '', gifLinks = []) {
  if (!gifLinks.length || !value) return value
  let result = value
  gifLinks.forEach((gif) => {
    const pattern = new RegExp(gif.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
    result = result.replace(pattern, '')
  })
  return result.trim()
}

export function isGifContent(value = '') {
  return detectGifLinks(value).length > 0
}

export function isEmojiOnly(value = '') {
  if (!value) return false
  const trimmed = value.trim()
  if (!trimmed) return false
  try {
    return EMOJI_ONLY_REGEX.test(trimmed)
  } catch {
    return false
  }
}

export function renderRichText(value = '') {
  if (!value) return ''
  const escaped = escapeHtml(value)
  const linked = escaped.replace(URL_REGEX, (match) => {
    const safe = match.replace(/"/g, '')
    return `<a href="${safe}" target="_blank" rel="noopener noreferrer">${safe}</a>`
  })
  return linked.replace(/\n/g, '<br>')
}
