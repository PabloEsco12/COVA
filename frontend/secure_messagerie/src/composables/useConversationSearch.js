import { nextTick, reactive, ref, watch } from 'vue'
import { searchConversationMessages as fetchConversationMessages } from '@/services/conversations'

/**
 * Encapsulates the state and helpers required to search within the current conversation.
 * All behaviour mirrors the original inline logic from MessagesView.vue so the UI remains unchanged.
 */
export function useConversationSearch({
  messages,
  selectedConversationId,
  normalizeMessage,
  extractError,
  selectConversation,
  ensureMessageVisible,
  scrollToMessage,
  searchConversationMessages = fetchConversationMessages,
} = {}) {
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

  function resetSearchPanel() {
    messageSearch.query = ''
    messageSearch.results = []
    messageSearch.error = ''
    messageSearch.executed = false
  }

  function stripDiacritics(value) {
    return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  }

  function normalizeSearchText(value) {
    return stripDiacritics(String(value || '')).toLowerCase()
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

  function resolveMessageList() {
    if (messages && Array.isArray(messages.value)) {
      return messages.value
    }
    return []
  }

  function searchLocalMessages(query, limit = 50) {
    const needle = normalizeSearchText(query)
    if (!needle) return []
    const results = []
    const source = resolveMessageList()
    for (let i = source.length - 1; i >= 0; i -= 1) {
      const message = source[i]
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
    if (!selectedConversationId?.value) return
    const query = String(messageSearch.query || '').trim()
    if (!query) {
      messageSearch.error = 'Entrez un mot-clé.'
      messageSearch.results = []
      return
    }
    messageSearch.loading = true
    messageSearch.error = ''
    try {
      let rawResults = []
      if (typeof searchConversationMessages === 'function') {
        const data = await searchConversationMessages(selectedConversationId.value, { query, limit: 50 })
        rawResults = extractSearchResults(data)
      }
      if (rawResults.length) {
        messageSearch.results = rawResults.map((entry) =>
          typeof normalizeMessage === 'function' ? normalizeMessage(entry) : entry,
        )
      } else {
        const fallback = searchLocalMessages(query, 50)
        messageSearch.results = fallback.slice()
        if (!fallback.length) {
          messageSearch.error = 'Aucun message trouvé.'
        }
      }
    } catch (err) {
      if (typeof extractError === 'function') {
        messageSearch.error = extractError(err, 'Recherche impossible.')
      } else {
        messageSearch.error = 'Recherche impossible.'
      }
    } finally {
      messageSearch.loading = false
      messageSearch.executed = true
    }
  }

  async function jumpToSearchResult(result) {
    if (!result) return
    if (
      result.conversationId &&
      result.conversationId !== selectedConversationId?.value &&
      typeof selectConversation === 'function'
    ) {
      await selectConversation(result.conversationId)
    }
    const streamPosition = result.streamPosition ?? null
    if (typeof ensureMessageVisible === 'function') {
      await ensureMessageVisible(result.id, streamPosition)
    }
    await nextTick()
    if (typeof scrollToMessage === 'function' && result.id) {
      scrollToMessage(result.id)
    }
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
