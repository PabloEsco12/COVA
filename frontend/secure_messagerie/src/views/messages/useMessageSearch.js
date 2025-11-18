import { nextTick, reactive, ref, watch } from 'vue'

export function useMessageSearch({
  stripDiacritics,
  normalizeMessage,
  searchConversationMessages,
  messages,
  selectedConversationId,
  ensureMessageVisible,
  selectConversation,
  scrollToMessage,
  extractError,
}) {
  const showSearchPanel = ref(false)
  const messageSearch = reactive({
    query: '',
    results: [],
    loading: false,
    error: '',
    executed: false,
  })

  watch(
    () => messageSearch.query,
    () => {
      messageSearch.executed = false
      messageSearch.error = ''
    },
  )

  function resetSearchPanel() {
    messageSearch.query = ''
    messageSearch.results = []
    messageSearch.error = ''
    messageSearch.executed = false
  }

  function toggleSearchPanel() {
    showSearchPanel.value = !showSearchPanel.value
    if (!showSearchPanel.value) {
      resetSearchPanel()
    }
  }

  function closeSearchPanel() {
    showSearchPanel.value = false
    resetSearchPanel()
  }

  function extractSearchResults(payload) {
    if (!payload) return []
    if (Array.isArray(payload)) return payload
    const candidates = ['results', 'items', 'messages', 'data']
    for (const key of candidates) {
      const value = payload[key]
      if (Array.isArray(value)) return value
      if (value && Array.isArray(value.items)) return value.items
    }
    return []
  }

  function normalizeSearchText(value) {
    return stripDiacritics(String(value || '')).toLowerCase()
  }

  function searchLocalMessages(query, limit = 50) {
    const needle = normalizeSearchText(query)
    if (!needle) return []
    const results = []
    for (let i = messages.value.length - 1; i >= 0; i -= 1) {
      const message = messages.value[i]
      if (!message || message.deleted) continue
      const parts = [
        message.content,
        message.displayName,
        Array.isArray(message.attachments) ? message.attachments.map((att) => att.fileName).join(' ') : '',
      ].filter(Boolean)
      const haystack = normalizeSearchText(parts.join(' '))
      if (haystack && haystack.includes(needle)) {
        results.push(message)
        if (results.length >= limit) break
      }
    }
    return results.reverse()
  }

  async function performMessageSearch() {
    if (!selectedConversationId.value) return
    const query = messageSearch.query.trim()
    if (!query) {
      messageSearch.error = 'Entrez un mot-clé.'
      messageSearch.results = []
      return
    }
    messageSearch.loading = true
    messageSearch.error = ''
    try {
      const data = await searchConversationMessages(selectedConversationId.value, { query, limit: 50 })
      const rawResults = extractSearchResults(data)
      if (rawResults.length) {
        messageSearch.results = rawResults.map((entry) => normalizeMessage(entry))
      } else {
        const fallback = searchLocalMessages(query, 50)
        messageSearch.results = fallback.slice()
        if (!fallback.length) {
          messageSearch.error = 'Aucun message trouvé.'
        }
      }
    } catch (err) {
      messageSearch.error = extractError(err, 'Recherche impossible.')
    } finally {
      messageSearch.loading = false
      messageSearch.executed = true
    }
  }

  async function jumpToSearchResult(result) {
    if (!result) return
    if (result.conversationId && result.conversationId !== selectedConversationId.value) {
      await selectConversation(result.conversationId)
    }
    const streamPosition = result.streamPosition ?? null
    await ensureMessageVisible(result.id, streamPosition)
    await nextTick()
    scrollToMessage(result.id)
    showSearchPanel.value = false
    resetSearchPanel()
  }

  return {
    showSearchPanel,
    messageSearch,
    toggleSearchPanel,
    closeSearchPanel,
    resetSearchPanel,
    performMessageSearch,
    jumpToSearchResult,
  }
}
