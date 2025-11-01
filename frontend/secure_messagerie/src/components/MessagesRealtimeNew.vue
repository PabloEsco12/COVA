<template>
  <div class="chat-page">
    <aside class="chat-sidebar">
      <header class="sidebar-header">
        <div>
          <h2>Conversations</h2>
          <p class="sidebar-subtitle">Messages chiffrés en temps réel</p>
        </div>
        <button
          type="button"
          class="icon-button"
          :disabled="loadingConversations"
          @click="loadConversations"
        >
          <span class="icon" aria-hidden="true">⟳</span>
          <span class="sr-only">Rafraîchir les conversations</span>
        </button>
      </header>

      <p v-if="globalError" class="error-banner">{{ globalError }}</p>

      <div class="sidebar-content">
        <p v-if="loadingConversations" class="placeholder">Chargement des conversations…</p>
        <p v-else-if="sortedConversations.length === 0" class="placeholder">
          Aucune conversation disponible.
        </p>
        <ul v-else class="conversation-list">
          <li
            v-for="conversation in sortedConversations"
            :key="conversation.id"
            :class="[
              'conversation-item',
              { active: conversation.id === selectedConversationId }
            ]"
            @click="selectConversation(conversation.id)"
          >
            <div class="conversation-main">
              <h3 class="conversation-title">
                {{ conversationDisplayName(conversation) }}
              </h3>
              <p class="conversation-preview">
                {{ conversationPreview(conversation) }}
              </p>
            </div>
            <div class="conversation-meta">
              <time
                v-if="conversation.updated_at"
                class="conversation-time"
                :datetime="conversation.updated_at"
              >
                {{ formatShortTimestamp(conversation.updated_at) }}
              </time>
              <span
                v-if="getUnreadCount(conversation.id) > 0"
                class="unread-count"
              >
                {{ getUnreadCount(conversation.id) }}
              </span>
            </div>
          </li>
        </ul>
      </div>
    </aside>

    <section class="chat-content">
      <div v-if="selectedConversation" class="chat-container">
        <header class="chat-header">
          <div>
            <h3>{{ conversationDisplayName(selectedConversation) }}</h3>
            <p class="chat-subtitle">{{ conversationSubtitle(selectedConversation) }}</p>
          </div>
          <div class="chat-header-actions">
            <p v-if="connectionError" class="error-inline">{{ connectionError }}</p>
            <button
              type="button"
              class="link-button"
              :disabled="loadingMessages"
              @click="reloadMessages"
            >
              Actualiser
            </button>
          </div>
        </header>

        <div ref="messagesContainer" class="messages-scroll" @scroll="handleScroll">
          <p v-if="loadingMessages" class="placeholder">Chargement des messages…</p>
          <p v-else-if="messages.length === 0" class="placeholder">
            Aucun message pour l'instant. Envoyez le premier !
          </p>
          <div
            v-else
            v-for="message in messages"
            :key="message.id"
            :class="['message-row', { mine: message.isMine }]"
          >
            <div class="message-bubble">
              <div class="message-meta">
                <span class="author">{{ messageAuthorLabel(message) }}</span>
                <time class="timestamp" :datetime="message.created_at">
                  {{ formatTimestamp(message.created_at) }}
                </time>
              </div>
              <p class="message-content">{{ message.text }}</p>
            </div>
          </div>
        </div>

        <form class="composer" @submit.prevent="handleSend">
          <textarea
            v-model="newMessage"
            rows="2"
            :disabled="sendingMessage || !selectedConversationId"
            placeholder="Écrivez votre message…"
          ></textarea>
          <div class="composer-actions">
            <span v-if="sendError" class="error-inline">{{ sendError }}</span>
            <button type="submit" :disabled="sendDisabled">
              {{ sendingMessage ? 'Envoi…' : 'Envoyer' }}
            </button>
          </div>
        </form>
      </div>
      <div v-else class="chat-placeholder">
        <h3>Bienvenue</h3>
        <p>Sélectionnez une conversation dans la liste pour commencer.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import { backendBase } from '@/utils/api'
import { ConversationSocket } from '@/services/socketService'
import {
  listConversations,
  listConversationMessages,
  markConversationMessagesRead,
  sendConversationMessage,
} from '@/services/messagingService'

const conversations = ref([])
const messages = ref([])
const selectedConversationId = ref(null)
const loadingConversations = ref(false)
const loadingMessages = ref(false)
const sendingMessage = ref(false)
const globalError = ref('')
const sendError = ref('')
const connectionError = ref('')
const newMessage = ref('')
const messagesContainer = ref(null)
const stickToBottom = ref(true)

const currentUserId = (localStorage.getItem('user_id') || '').toString()
const normalizedCurrentUserId = normalizeId(currentUserId)

const unreadCounts = reactive({})
let socketClient = null

const sortedConversations = computed(() => {
  const items = [...conversations.value]
  return items.sort((a, b) => {
    const at = a.updated_at ? new Date(a.updated_at).getTime() : 0
    const bt = b.updated_at ? new Date(b.updated_at).getTime() : 0
    return bt - at
  })
})

const selectedConversation = computed(() =>
  conversations.value.find(conv => conv.id === selectedConversationId.value) || null,
)

const sendDisabled = computed(
  () =>
    sendingMessage.value ||
    !selectedConversationId.value ||
    !newMessage.value ||
    newMessage.value.trim().length === 0,
)

watch(
  () => messages.value.length,
  async (current, previous) => {
    if (current === 0 || current === previous) return
    await nextTick()
    if (stickToBottom.value) {
      scrollToBottom()
    }
  },
)

watch(newMessage, () => {
  if (sendError.value) sendError.value = ''
})

function normalizeId(value) {
  if (value == null) return ''
  return String(value).toLowerCase()
}

function getUnreadCount(conversationId) {
  const key = String(conversationId)
  return unreadCounts[key] || 0
}

function setUnreadCount(conversationId, count) {
  const key = String(conversationId)
  if (count <= 0) delete unreadCounts[key]
  else unreadCounts[key] = count
}

function incrementUnread(conversationId) {
  const key = String(conversationId)
  unreadCounts[key] = (unreadCounts[key] || 0) + 1
}

function extractMessageText(content) {
  if (!content) return ''
  if (typeof content === 'string') return content
  if (typeof content.text === 'string' && content.text.trim()) return content.text.trim()
  if (typeof content.message === 'string' && content.message.trim()) return content.message.trim()
  return ''
}

function enrichMessage(raw) {
  const reads = Array.isArray(raw.reads)
    ? raw.reads.map(receipt => ({
        message_id: receipt.message_id,
        user_id: receipt.user_id,
        user: receipt.user || null,
        read_at: receipt.read_at,
      }))
    : []

  return {
    id: raw.id,
    conversation_id: raw.conversation_id,
    author_id: raw.author_id,
    author: raw.author || null,
    content_json: raw.content_json || {},
    created_at: raw.created_at,
    updated_at: raw.updated_at,
    state: raw.state,
    reads,
    text: extractMessageText(raw.content_json),
    isMine: normalizeId(raw.author_id) === normalizedCurrentUserId,
  }
}

function conversationDisplayName(conversation) {
  if (!conversation) return ''
  if (conversation.title) return conversation.title
  const members = Array.isArray(conversation.members) ? conversation.members : []
  const others = members
    .filter(member => normalizeId(member.user_id) !== normalizedCurrentUserId)
    .map(member => member.user?.display_name || member.user?.email || 'Contact')
  if (others.length === 1) return others[0]
  if (others.length > 1) return others.join(', ')
  return conversation.topic || 'Conversation'
}

function conversationSubtitle(conversation) {
  const members = Array.isArray(conversation.members) ? conversation.members.length : 0
  if (members <= 1) return 'Conversation privée'
  return `${members} participants`
}

function conversationPreview(conversation) {
  if (!conversation) return ''
  if (conversation.lastMessagePreview) return conversation.lastMessagePreview
  if (conversation.topic) return conversation.topic
  return 'Conversation'
}

function messageAuthorLabel(message) {
  if (message.isMine) return 'Vous'
  return message.author?.display_name || message.author?.email || 'Participant'
}

function formatTimestamp(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  return date.toLocaleString('fr-BE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

function formatShortTimestamp(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  return date.toLocaleDateString('fr-BE', { day: '2-digit', month: '2-digit' })
}

function scrollToBottom() {
  const container = messagesContainer.value
  if (!container) return
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
}

function handleScroll() {
  const container = messagesContainer.value
  if (!container) return
  const threshold = 48
  stickToBottom.value =
    container.scrollTop + container.clientHeight >= container.scrollHeight - threshold
}

async function loadConversations() {
  loadingConversations.value = true
  try {
    const data = await listConversations()
    conversations.value = (data || []).map(conv => ({
      ...conv,
      lastMessagePreview: conv.lastMessagePreview || '',
    }))
    globalError.value = ''
    if (!selectedConversationId.value && conversations.value.length > 0) {
      await selectConversation(conversations.value[0].id)
    }
  } catch (error) {
    console.error('Unable to load conversations', error)
    globalError.value = "Impossible de charger les conversations."
  } finally {
    loadingConversations.value = false
  }
}

async function selectConversation(conversationId) {
  if (!conversationId || selectedConversationId.value === conversationId) return
  selectedConversationId.value = conversationId
  await Promise.all([loadMessages(conversationId), connectRealtime(conversationId)])
}

async function reloadMessages() {
  if (!selectedConversationId.value) return
  await loadMessages(selectedConversationId.value, { scroll: false })
}

function updateConversationMetadata(conversationId, message) {
  const index = conversations.value.findIndex(conv => conv.id === conversationId)
  if (index === -1) {
    // Conversation might be new, refresh the list
    loadConversations()
    return
  }
  const current = conversations.value[index]
  conversations.value[index] = {
    ...current,
    updated_at: message.created_at || message.updated_at || current.updated_at,
    lastMessagePreview: message.text || current.lastMessagePreview,
  }
}

function upsertMessage(message) {
  const existingIndex = messages.value.findIndex(item => item.id === message.id)
  if (existingIndex === -1) {
    messages.value = [...messages.value, message].sort(
      (a, b) => new Date(a.created_at) - new Date(b.created_at),
    )
  } else {
    messages.value.splice(existingIndex, 1, message)
  }
}

async function loadMessages(conversationId, options = { scroll: true }) {
  if (!conversationId) return
  loadingMessages.value = true
  try {
    const data = await listConversationMessages(conversationId)
    messages.value = (data || []).map(enrichMessage)
    const last = messages.value[messages.value.length - 1]
    if (last) {
      updateConversationMetadata(conversationId, last)
    }
    if (options.scroll !== false) {
      await nextTick()
      scrollToBottom()
    }
    await markCurrentConversationRead()
    connectionError.value = ''
  } catch (error) {
    console.error('Unable to load messages', error)
    connectionError.value = "Échec du chargement des messages."
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

async function handleSend() {
  if (sendDisabled.value) return
  const conversationId = selectedConversationId.value
  const text = newMessage.value.trim()
  if (!conversationId || !text) return

  sendingMessage.value = true
  sendError.value = ''
  try {
    const payload = { content_json: { text } }
    const saved = await sendConversationMessage(conversationId, payload)
    const message = enrichMessage(saved)
    upsertMessage(message)
    updateConversationMetadata(conversationId, message)
    newMessage.value = ''
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Unable to send message', error)
    sendError.value = "L'envoi du message a échoué."
  } finally {
    sendingMessage.value = false
  }
}

async function markCurrentConversationRead() {
  const conversationId = selectedConversationId.value
  if (!conversationId) return
  const unreadMessages = messages.value.filter(message => {
    if (message.isMine) return false
    return !message.reads?.some(receipt => normalizeId(receipt.user_id) === normalizedCurrentUserId)
  })

  if (unreadMessages.length === 0) {
    setUnreadCount(conversationId, 0)
    return
  }

  try {
    const identifiers = unreadMessages.map(message => message.id)
    await markConversationMessagesRead(conversationId, identifiers)
    setUnreadCount(conversationId, 0)
  } catch (error) {
    console.error('Unable to mark messages as read', error)
  }
}

async function connectRealtime(conversationId) {
  if (!conversationId) return
  if (!socketClient) {
    socketClient = new ConversationSocket({
      baseUrl: backendBase,
      tokenProvider: () => localStorage.getItem('access_token') || '',
    })
    socketClient.on('message', handleRealtimeMessage)
    socketClient.on('read', handleRealtimeRead)
    socketClient.on('close', () => {
      connectionError.value = 'Connexion temps réel interrompue.'
    })
    socketClient.on('error', error => {
      console.error('Realtime error', error)
      connectionError.value = 'Erreur de connexion temps réel.'
    })
    socketClient.on('ack', () => {
      connectionError.value = ''
    })
  }

  try {
    await socketClient.connect(conversationId)
  } catch (error) {
    console.error('Unable to connect realtime', error)
    connectionError.value = 'Impossible de se connecter au flux temps réel.'
  }
}

function handleRealtimeMessage(payload) {
  if (!payload || payload.type !== 'message.created') return
  const conversationId = payload.conversation_id
  const raw = payload.message
  if (!conversationId || !raw) return
  const message = enrichMessage(raw)
  updateConversationMetadata(conversationId, message)

  if (conversationId === selectedConversationId.value) {
    upsertMessage(message)
    if (!message.isMine) markCurrentConversationRead()
  } else if (!message.isMine) {
    incrementUnread(conversationId)
  }
}

function handleRealtimeRead(payload) {
  if (!payload || payload.type !== 'message.read') return
  const { conversation_id: conversationId, message_ids: messageIds, user_id: userId, published_at: publishedAt } =
    payload
  if (!conversationId || !Array.isArray(messageIds) || !userId) return
  if (conversationId !== selectedConversationId.value) {
    if (normalizeId(userId) === normalizedCurrentUserId) {
      setUnreadCount(conversationId, 0)
    }
    return
  }

  for (const identifier of messageIds) {
    const entry = messages.value.find(message => message.id === identifier)
    if (!entry) continue
    if (!entry.reads) entry.reads = []
    const already = entry.reads.some(receipt => normalizeId(receipt.user_id) === normalizeId(userId))
    if (!already) {
      entry.reads.push({
        message_id: entry.id,
        user_id: userId,
        read_at: publishedAt || new Date().toISOString(),
        user: null,
      })
    }
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    markCurrentConversationRead()
  }
}

onMounted(async () => {
  await loadConversations()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onBeforeUnmount(async () => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (socketClient) {
    await socketClient.disconnect()
  }
  socketClient = null
})
</script>

<style scoped src="../styles/components/MessagesRealtimeNew.css"></style>
