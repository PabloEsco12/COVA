// ===== Message Content Helpers =====
// Regroupe les outils de parsing pour l'affichage texte: detection GIF, nettoyage des URLs et rendu HTML securise.

// ---- Expressions regulieres cles ----
// URL_REGEX : capture les liens pour les transformer en <a> cliquables.
// URL_CHECK_REGEX : verifie si un token est exactement une URL (pas de texte autour).
// GIF_HINT_REGEX : repere les liens pointant vers un GIF (tenor/giphy ou extension .gif).
// GIF_CLEANUP_REGEX : supprime les caracteres invisibles eventuels.
// EMOJI_ONLY_REGEX : determine si un message est compose exclusivement d'emojis.
const URL_REGEX = /(https?:\/\/[^\s]+)/gi
const URL_CHECK_REGEX = /^https?:\/\/[^\s]+$/i
const GIF_HINT_REGEX = /(tenor\.com|giphy\.com|\.gif($|\?))/i
const GIF_CLEANUP_REGEX = /[\u200B-\u200D\uFEFF]/g
const EMOJI_ONLY_REGEX = /^[\p{Extended_Pictographic}\u200d\s]+$/u

// ---- Echappement HTML ----
// Protege le texte brut pour empecher les injections lors du rendu Rich Text.
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// ---- Detection des GIFs ----
// Retourne la liste unique des liens GIF presents dans une chaine (utile pour les previsualisations).
export function detectGifLinks(value = '') {
  if (!value) return []
  const candidates = value.split(/\s+/).filter(Boolean)
  const links = candidates
    .map((token) => token.trim().replace(GIF_CLEANUP_REGEX, ''))
    .filter((token) => URL_CHECK_REGEX.test(token) && GIF_HINT_REGEX.test(token))
  return [...new Set(links)]
}

// ---- Nettoyage des GIFs ----
// Retire les liens GIF detectes du message tout en conservant le reste du texte.
export function stripGifLinks(value = '', gifLinks = []) {
  if (!gifLinks.length || !value) return value
  let result = value
  gifLinks.forEach((gif) => {
    const pattern = new RegExp(gif.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
    result = result.replace(pattern, '')
  })
  return result.trim()
}

// ---- Classification rapide ----
// isGifContent : indique si un message contient au moins un lien GIF.
export function isGifContent(value = '') {
  return detectGifLinks(value).length > 0
}

// isEmojiOnly : detecte les messages composes uniquement d'emojis (pour adapter la taille d'affichage par ex.).
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

// ---- Mappage des pieces jointes optimistes ----
// Uniformise la forme des pieces jointes encore en upload pour l'affichage immediat cote client.
export function mapOptimisticAttachments(list = []) {
  return list.map((entry) => ({
    id: entry.id,
    name: entry.descriptor?.file_name || entry.name || 'Fichier',
    size: entry.descriptor?.file_size || entry.size || 0,
    url: entry.descriptor?.upload_url || entry.url || null,
    status: entry.status || 'ready',
    descriptor: entry.descriptor || null,
    mime_type: entry.descriptor?.mime_type || entry.mime_type || '',
  }))
}

// ---- Rendu Rich Text ----
// Echappe le texte, convertit les URLs en liens cliquables et remplace les retours lignes par <br>.
export function renderRichText(value = '') {
  if (!value) return ''
  const escaped = escapeHtml(value)
  const linked = escaped.replace(URL_REGEX, (match) => {
    const safe = match.replace(/"/g, '')
    return `<a href="${safe}" target="_blank" rel="noopener noreferrer">${safe}</a>`
  })
  return linked.replace(/\n/g, '<br>')
}
