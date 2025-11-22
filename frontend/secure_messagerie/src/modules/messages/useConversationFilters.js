import { computed, ref } from 'vue'

const DEFAULT_FILTERS = [
  { value: 'all', label: 'Toutes', icon: 'bi bi-inbox' },
  { value: 'unread', label: 'Non lues', icon: 'bi bi-envelope-open' },
  { value: 'direct', label: 'Direct', icon: 'bi bi-person' },
  { value: 'group', label: 'Groupes', icon: 'bi bi-people' },
]

const DEFAULT_ROLES = [
  { value: 'owner', label: 'Propriétaire' },
  { value: 'moderator', label: 'Modérateur' },
  { value: 'member', label: 'Membre' },
  { value: 'guest', label: 'Invité' },
]

export function useConversationFilters({
  conversations,
  conversationMeta,
  loadingConversations,
  conversationPresence,
  defaultPresenceLabel = 'Hors ligne',
}) {
  const conversationSearch = ref('')
  const conversationFilter = ref('all')
  const conversationFilters = DEFAULT_FILTERS
  const conversationRoles = DEFAULT_ROLES

  const conversationSummary = computed(() => {
    if (loadingConversations.value) return 'Chargement...'
    const count = conversations.value.length
    return count ? `${count} conversation${count > 1 ? 's' : ''}` : 'Aucune conversation'
  })

  const sortedConversations = computed(() => {
    const term = conversationSearch.value.trim().toLowerCase()
    const presenceMap = conversationPresence?.value ?? conversationPresence ?? {}
    const list = conversations.value.map((conv) => {
      const meta = conversationMeta[conv.id] || {}
      const presence = presenceMap[conv.id] || {}
      return {
        ...conv,
        unreadCount: meta.unreadCount || 0,
        lastPreview: meta.lastPreview || '',
        lastActivity: meta.lastActivity || conv.createdAt,
        avatarUrl: meta.avatarUrl ?? conv.avatarUrl ?? null,
        presenceStatus: presence.status || 'offline',
        presenceLabel: presence.label || defaultPresenceLabel,
      }
    })
    let filtered = list
    if (conversationFilter.value === 'unread') {
      filtered = filtered.filter((conv) => conv.unreadCount > 0)
    } else if (conversationFilter.value === 'direct') {
      filtered = filtered.filter((conv) => conv.participants.length <= 1)
    } else if (conversationFilter.value === 'group') {
      filtered = filtered.filter((conv) => conv.participants.length > 1)
    }
    if (term) {
      filtered = filtered.filter(
        (conv) =>
          conv.displayName.toLowerCase().includes(term) ||
          (conv.lastPreview || '').toLowerCase().includes(term),
      )
    }
    return filtered.sort((a, b) => new Date(b.lastActivity) - new Date(a.lastActivity))
  })

  const activeFilterLabel = computed(() => {
    const option = conversationFilters.find((filter) => filter.value === conversationFilter.value)
    return option ? option.label : 'Toutes'
  })

  return {
    conversationSearch,
    conversationFilter,
    conversationFilters,
    conversationRoles,
    conversationSummary,
    sortedConversations,
    activeFilterLabel,
  }
}
