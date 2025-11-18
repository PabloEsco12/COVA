import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { fetchGifs, hasGifApiSupport } from '@/services/media'
import { emojiSections, emojiCatalog } from '@/utils/reactions'

export function useComposerTools({
  gifLibrary,
  selectedConversationId,
  uploadAttachment,
  extractError,
  messageInput,
}) {
  const attachmentInput = ref(null)
  const pendingAttachments = ref([])
  const attachmentError = ref('')
  const composerState = reactive({
    mode: 'new', // new | reply | forward | edit
    targetMessageId: null,
    replyTo: null,
    forwardFrom: null,
  })
  const showPicker = ref(false)
  const pickerMode = ref('emoji')
  const emojiSearch = ref('')
  const gifSearch = ref('')
  const gifResults = ref(gifLibrary.slice())
  const loadingGifs = ref(false)
  const gifError = ref('')
  const gifSearchAvailable = hasGifApiSupport()
  let gifSearchTimer = null

  async function loadGifResults(query = '') {
    if (!gifSearchAvailable) {
      gifResults.value = gifLibrary
      return
    }
    loadingGifs.value = true
    gifError.value = ''
    try {
      const gifs = await fetchGifs({ query, limit: 30 })
      gifResults.value = gifs.length ? gifs : gifLibrary
    } catch (err) {
      gifError.value = err?.message || 'Impossible de charger les GIFs.'
      gifResults.value = gifLibrary
    } finally {
      loadingGifs.value = false
    }
  }

  watch(
    [showPicker, pickerMode],
    ([visible, mode]) => {
      if (visible && mode === 'gif') {
        loadGifResults(gifSearch.value)
      }
    },
    { flush: 'post' },
  )

  watch(gifSearch, (term) => {
    if (pickerMode.value !== 'gif' || !showPicker.value) return
    if (gifSearchTimer) clearTimeout(gifSearchTimer)
    gifSearchTimer = setTimeout(() => {
      loadGifResults(term)
    }, 350)
  })

  onBeforeUnmount(() => {
    if (gifSearchTimer) {
      clearTimeout(gifSearchTimer)
      gifSearchTimer = null
    }
  })

  function togglePicker() {
    showPicker.value = !showPicker.value
    if (showPicker.value) {
      pickerMode.value = 'emoji'
      emojiSearch.value = ''
      gifSearch.value = ''
      gifError.value = ''
    } else {
      emojiSearch.value = ''
      gifSearch.value = ''
      gifError.value = ''
      loadingGifs.value = false
      gifResults.value = gifLibrary.slice()
    }
  }

  function setPickerMode(mode) {
    pickerMode.value = mode
    showPicker.value = true
    if (mode !== 'emoji') {
      emojiSearch.value = ''
    }
    if (mode === 'gif') {
      loadGifResults(gifSearch.value)
    }
  }

  function resetComposerState() {
    composerState.mode = 'new'
    composerState.targetMessageId = null
    composerState.replyTo = null
    composerState.forwardFrom = null
  }

  function startReply(message) {
    if (!message) return
    composerState.mode = 'reply'
    composerState.replyTo = message
    composerState.forwardFrom = null
    composerState.targetMessageId = null
  }

  function startForward(message) {
    if (!message) return
    composerState.mode = 'forward'
    composerState.forwardFrom = message
    composerState.replyTo = null
    composerState.targetMessageId = null
    if (!messageInput.value) {
      messageInput.value = message.content || ''
    }
  }

  function startEdit(message) {
    if (!message) return
    composerState.mode = 'edit'
    composerState.targetMessageId = message.id
    composerState.replyTo = null
    composerState.forwardFrom = null
    messageInput.value = message.content || ''
    clearPendingAttachments()
  }

  function cancelComposerContext() {
    resetComposerState()
  }

  function triggerAttachmentPicker() {
    attachmentError.value = ''
    if (!selectedConversationId.value) {
      attachmentError.value = "Sélectionnez une conversation avant d'ajouter un fichier."
      return
    }
    if (attachmentInput.value) {
      attachmentInput.value.value = ''
      attachmentInput.value.click()
    }
  }

  function onAttachmentChange(event) {
    const files = Array.from(event.target?.files || [])
    if (!files.length) return
    files.forEach((file) => queueAttachment(file))
  }

  function queueAttachment(file) {
    if (!file) return
    const entry = reactive({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
      status: 'uploading',
      progress: 0,
      descriptor: null,
      error: '',
    })
    pendingAttachments.value.push(entry)
    uploadAttachmentFile(entry)
  }

  async function uploadAttachmentFile(entry) {
    if (!selectedConversationId.value) {
      entry.status = 'error'
      entry.error = 'Aucune conversation active.'
      return
    }
    attachmentError.value = ''
    try {
      const descriptor = await uploadAttachment(selectedConversationId.value, entry.file, {
        onUploadProgress: (event) => {
          if (!event || !event.total) return
          entry.progress = Math.min(100, Math.round((event.loaded / event.total) * 100))
        },
      })
      entry.descriptor = descriptor
      entry.status = 'ready'
      entry.progress = 100
    } catch (err) {
      entry.status = 'error'
      entry.error = extractError(err, 'Impossible de téléverser le fichier.')
      attachmentError.value = entry.error
    }
  }

  function removeAttachment(entryId) {
    pendingAttachments.value = pendingAttachments.value.filter((entry) => entry.id !== entryId)
  }

  function clearPendingAttachments() {
    pendingAttachments.value = []
    attachmentError.value = ''
  }

  const filteredEmojiSections = computed(() => {
    const term = emojiSearch.value.trim().toLowerCase()
    if (!term) return emojiSections
    const matches = emojiSections
      .map((section) => ({
        ...section,
        items: section.items.filter((emoji) => emoji.toLowerCase().includes(term)),
      }))
      .filter((section) => section.items.length)
    if (matches.length) return matches
    return [
      {
        id: 'search',
        label: 'Résultats',
        items: emojiCatalog.filter((emoji) => emoji.toLowerCase().includes(term)),
      },
    ]
  })

  const displayedGifs = computed(() => (gifResults.value.length ? gifResults.value : gifLibrary))

  return {
    attachmentInput,
    pendingAttachments,
    attachmentError,
    composerState,
    showPicker,
    pickerMode,
    emojiSearch,
    gifSearch,
    gifResults,
    filteredEmojiSections,
    displayedGifs,
    loadingGifs,
    gifError,
    gifSearchAvailable,
    togglePicker,
    setPickerMode,
    resetComposerState,
    startReply,
    startForward,
    startEdit,
    cancelComposerContext,
    triggerAttachmentPicker,
    onAttachmentChange,
    queueAttachment,
    uploadAttachmentFile,
    removeAttachment,
    clearPendingAttachments,
    loadGifResults,
  }
}
