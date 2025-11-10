const TENOR_API_BASE = 'https://tenor.googleapis.com/v2'
const TENOR_API_KEY = import.meta.env.VITE_TENOR_API_KEY || ''
const TENOR_CLIENT = 'secure-messagerie'

function buildTenorUrl(endpoint, params) {
  const url = new URL(`${TENOR_API_BASE}/${endpoint}`)
  url.searchParams.set('key', TENOR_API_KEY)
  url.searchParams.set('client_key', TENOR_CLIENT)
  url.searchParams.set('media_filter', 'gif')
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })
  return url.toString()
}

export async function fetchGifs({ query = '', limit = 24 } = {}) {
  if (!TENOR_API_KEY) {
    throw new Error('Tenor API key missing (VITE_TENOR_API_KEY).')
  }
  const endpoint = query ? 'search' : 'featured'
  const url = buildTenorUrl(endpoint, {
    q: query || undefined,
    limit: String(limit),
  })
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('Unable to fetch GIFs')
  }
  const payload = await response.json()
  const results = Array.isArray(payload?.results) ? payload.results : []
  return results
    .map((item) => {
      const media = item.media_formats || {}
      const gif = media.gif || media.mediumgif || media.tinygif || media.nanogif
      const preview = media.nanogif || media.tinygif || gif
      if (!gif?.url) return null
      return {
        id: item.id,
        label: item.content_description || 'GIF',
        url: gif.url,
        preview: preview?.url || gif.url,
      }
    })
    .filter(Boolean)
}

export function hasGifApiSupport() {
  return Boolean(TENOR_API_KEY)
}
