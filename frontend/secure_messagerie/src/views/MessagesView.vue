<template>

  <div class="msg-shell">
    <MessageToastStack
      :toasts="messageToasts"
      :formatter="formatTime"
      @dismiss="dismissToast"
      @open="openToastConversation"
    />

    <div class="msg-layout">

      <ConversationSidebar
        :conversations="sortedConversations"
        :selected-id="selectedConversationId"
        :loading="loadingConversations"
        :error="conversationError"
        :summary="conversationSummary"
        :search="conversationSearch"
        :filter="conversationFilter"
        :filters="conversationFilters"
        @select="selectConversation"
        @new-conversation="goToNewConversation"
        @update:search="conversationSearch = $event"
        @update:filter="conversationFilter = $event"
        @avatar-error="onAvatarFailure"
      />

      <section class="msg-main">

        <MessageEmptyState v-if="!selectedConversation" @new="goToNewConversation" />
        <template v-else>
        <ChatHeader
          :title="selectedConversation.displayName"
          :subtitle="headerSubtitle"
          :avatar-url="selectedConversation.avatarUrl"
          :avatar-initials="selectedConversation.initials"
          :status="connectionStatus"
          :participant-status="primaryParticipantPresence.status"
          :participant-status-label="primaryParticipantPresence.label"
          :loading="loadingMessages"
          :show-refresh="false"
          :show-info="true"
          @info="openConversationPanel"
          @call="startCall('audio')"
          @video="startCall('video')"
        >
          <template #actions-left>
            <AvailabilityMenu
              :model-value="myAvailability"
              :options="availabilityOptions"
              @update:modelValue="onAvailabilityChange"
            />
            <button
              type="button"
              class="msg-main__icon"
              :class="{ active: showSearchPanel }"
              aria-label="Rechercher dans la conversation"
              @click="toggleSearchPanel"
            >
              <i class="bi bi-search"></i>
            </button>
          </template>
        </ChatHeader>
        <p v-if="messageError" class="msg-alert">{{ messageError }}</p>
        <MessageSearchPanel
          :show="showSearchPanel"
          :query="messageSearch.query"
          :loading="messageSearch.loading"
          :error="messageSearch.error"
          :results="messageSearch.results"
          :executed="messageSearch.executed"
          :format-absolute="formatAbsolute"
          :message-preview-text="messagePreviewText"
          @update:query="messageSearch.query = $event"
          @submit="performMessageSearch"
          @close="closeSearchPanel"
          @jump="jumpToSearchResult"
        />
        <MessageList
          ref="messageListRef"
          :messages="messages"
          :loading="loadingMessages"
          :loading-older="loadingOlderMessages"
          :pinned-messages="pinnedMessages"
          :reaction-palette="reactionPalette"
          :reaction-picker-for="reactionPickerFor"
          :message-menu-open="messageMenuOpen"
          :copied-id="copiedMessageId"
          :formatters="messageFormatters"
          :is-reaction-pending="isReactionPending"
          :is-pinning="isPinning"
          :can-moderate="isConversationOwner"
          @load-older="loadOlderMessages"
          @select-pin="scrollToMessage"
          @toggle-reaction-picker="toggleReactionPicker"
          @toggle-message-menu="toggleMessageMenu"
          @reaction-select="({ message, emoji }) => handleReactionSelection(message, emoji)"
          @reaction-toggle="({ message, emoji }) => toggleReaction(message, emoji)"
          @pin="handlePinToggle"
          @reply="startReply"
          @forward="initiateForward"
          @edit="startEdit"
          @delete="confirmDeleteMessage"
          @copy="copyMessage"
          @download-attachment="downloadAttachment"
        />

        <MessageComposer
          v-model:message-input="messageInput"
          :blocked-info="composerBlockedInfo"
          :show-picker="showPicker"
          :picker-mode="pickerMode"
          :emoji-search="emojiSearch"
          :gif-search="gifSearch"
          :gif-search-available="gifSearchAvailable"
          :filtered-emoji-sections="filteredEmojiSections"
          :displayed-gifs="displayedGifs"
          :gif-error="gifError"
          :loading-gifs="loadingGifs"
          :add-emoji="addEmoji"
          :insert-gif="insertGif"
          :on-emoji-search="(value) => { emojiSearch.value = value }"
          :on-gif-search="(value) => { gifSearch.value = value }"
          :attachment-input="attachmentInput"
          :on-attachment-change="onAttachmentChange"
          :sending="sending"
          :on-composer-input="onComposerInput"
          :handle-composer-blur="handleComposerBlur"
          :pending-attachments="pendingAttachments"
          :is-editing-message="isEditingMessage"
          :format-file-size="formatFileSize"
          :remove-attachment="removeAttachment"
          :attachment-error="attachmentError"
          :has-composer-context="hasComposerContext"
          :composer-state="composerState"
          :message-preview-text="messagePreviewText"
          :cancel-composer-context="cancelComposerContext"
          :typing-indicator-text="typingIndicatorText"
          :trigger-attachment-picker="triggerAttachmentPicker"
          :has-attachment-in-progress="hasAttachmentInProgress"
          :toggle-picker="togglePicker"
          :set-picker-mode="setPickerMode"
          :can-send="canSend"
          :send-message="sendMessage"
        />

        <DeleteMessageModal
          v-model:visible="deleteDialog.visible"
          :preview="deleteDialogPreview"
          :error="deleteDialog.error"
          :loading="deleteDialog.loading"
          @close="closeDeleteDialog"
          @confirm="performDeleteMessage"
        />

        <CallOverlay
          :call-state="callState"
          :call-controls="callControls"
          :call-status-label="callStatusLabel"
          :remote-display-name="remoteDisplayName"
          :local-video-ref="localVideoRef"
          :remote-video-ref="remoteVideoRef"
          :remote-audio-ref="remoteAudioRef"
          @accept="acceptIncomingCall"
          @reject="rejectIncomingCall"
          @cancel="cancelOutgoingCall"
          @hangup="hangupCall"
          @toggle-mic="toggleMicrophone"
          @toggle-camera="toggleCamera"
        />

      </template>

    </section>
  </div>
  <ConversationPanel
    :show="showConversationPanel"
    :selected-conversation="selectedConversation"
    :conversation-owner-summary="conversationOwnerSummary"
    :conversation-info-error="conversationInfoError"
    :conversation-info-notice="conversationInfoNotice"
    :conversation-form="conversationForm"
    :saving-conversation="savingConversation"
    :leaving-conversation="leavingConversation"
    :loading-invites="loadingInvites"
    :invites="invites"
    :invite-form="inviteForm"
    :invite-busy="inviteBusy"
    :invite-revoke-busy="inviteRevokeBusy"
    :member-busy="memberBusy"
    :can-manage-conversation="canManageConversation"
    :current-user-id="currentUserId"
    :conversation-roles="conversationRoles"
    :format-absolute="formatAbsolute"
    :role-label="roleLabel"
    :member-presence="memberPresence"
    :member-presence-text="memberPresenceText"
    :close-conversation-panel="closeConversationPanel"
    :save-conversation-settings="saveConversationSettings"
    :leave-current-conversation="leaveCurrentConversation"
    :submit-invite="submitInvite"
    :revoke-invite="revokeInvite"
    :update-member-role="updateMemberRole"
    :mute-member="muteMember"
    :unmute-member="unmuteMember"
    :remove-member="removeMember"
  />


  <ForwardPicker
    ref="forwardPickerRef"
    :open="forwardPicker.open"
    :message="forwardPicker.message"
    :preview="messagePreviewText(forwardPicker.message)"
    :query="forwardPicker.query"
    :targets="forwardPickerTargets"
    @update:query="forwardPicker.query = $event"
    @select="confirmForwardTarget"
    @cancel="cancelForwardSelection"
  />

</div>
</template>
<script setup>

import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import { useRoute, useRouter } from 'vue-router'
import { api, backendBase } from '@/utils/api'
import { createConversationSocket } from '@/services/realtime'
import { useNotificationsStream } from '@/composables/useNotificationsStream'
import { useConversationSearch } from '@/composables/useConversationSearch'
import {
  pinMessage,
  unpinMessage,
  updateMessageReaction,
  uploadAttachment,
  editConversationMessage,
  deleteConversationMessage,
} from '@/services/conversations'
import { fetchGifs, hasGifApiSupport } from '@/services/media'
import { emojiSections, emojiCatalog, defaultGifLibrary } from '@/utils/reactions'
import ConversationSidebar from '@/components/messages/ConversationSidebar.vue'
import ChatHeader from '@/components/messages/ChatHeader.vue'
import MessageList from '@/components/messages/MessageList.vue'
import AvailabilityMenu from '@/components/messages/AvailabilityMenu.vue'
import ConversationPanel from '@/components/messages/ConversationPanel.vue'
import CallOverlay from '@/components/messages/CallOverlay.vue'
import ForwardPicker from '@/components/messages/ForwardPicker.vue'
import MessageToastStack from '@/components/messages/MessageToastStack.vue'
import MessageComposer from '@/components/messages/MessageComposer.vue'
import MessageEmptyState from '@/components/messages/MessageEmptyState.vue'
import MessageSearchPanel from '@/components/messages/MessageSearchPanel.vue'
import DeleteMessageModal from '@/components/messages/DeleteMessageModal.vue'
import CustomModal from '@/components/ui/CustomModal.vue'
import { useMessageComposer } from '@/composables/useMessageComposer'
import { STATUS_LABELS, availabilityOptions } from '@/views/messages/constants'
import {
  formatTime,
  formatAbsolute,
  formatFileSize,
  messagePreviewText,
  extractDeliverySummary,
} from '@/views/messages/formatters'
import { createMessageFormatters } from '@/views/messages/message-formatters'
import { useAttachments } from '@/views/messages/useAttachments'
import { useMessageToasts } from '@/views/messages/useMessageToasts'
import { useCallControls } from '@/views/messages/useCallControls'
import { generateLocalId } from '@/views/messages/id'
import { useNotificationsBridge } from '@/views/messages/useNotificationsBridge'
import { useMessageNotifications } from '@/views/messages/useMessageNotifications'
import { useConversationPanel } from '@/views/messages/useConversationPanel'
import { useComposerContext } from '@/views/messages/useComposerContext'
import { useDeleteMessage } from '@/views/messages/useDeleteMessage'
import { memberUserId, normalizeMember, normalizeConversation, normalizeMessage } from '@/views/messages/mappers'
import { usePresenceStatus } from '@/views/messages/usePresenceStatus'


const gifLibrary = defaultGifLibrary


const conversations = ref([])
const conversationMeta = reactive({})

const conversationSearch = ref('')

const loadingConversations = ref(true)

const conversationError = ref('')

const unreadSummary = ref({ total: 0, conversations: [] })

const conversationFilter = ref('all')
const conversationFilters = [
  { value: 'all', label: 'Toutes', icon: 'bi bi-inbox' },
  { value: 'unread', label: 'Non lues', icon: 'bi bi-envelope-open' },
  { value: 'direct', label: 'Direct', icon: 'bi bi-person' },
  { value: 'group', label: 'Groupes', icon: 'bi bi-people' },
]
const conversationRoles = [
  { value: 'owner', label: 'Propriétaire' },
  { value: 'moderator', label: 'Modérateur' },
  { value: 'member', label: 'Membre' },
  { value: 'guest', label: 'Invité' },
]
let typingCleanupTimer = null
const selectedConversationId = ref(null)
const currentUserId = ref(localStorage.getItem('user_id') || null)
const notificationDedupSet = new Set()
const messageError = ref('')
const selectedConversation = computed(() => {
  if (!selectedConversationId.value) return null
  return conversations.value.find((conv) => conv.id === selectedConversationId.value) || null
})

const {
  myAvailability,
  conversationPresence,
  presenceSummary,
  primaryParticipantPresence,
  typingIndicatorText,
  memberPresence,
  memberPresenceText,
  resetPresenceState,
  applyPresencePayload,
  handleRealtimeTyping,
  cleanupRemoteTyping,
  loadAvailabilityStatus,
  onAvailabilityChange,
  handleProfileBroadcast,
  displayNameForUser,
} = usePresenceStatus({
  conversations,
  selectedConversation,
  selectedConversationId,
  currentUserId,
  formatAbsolute,
})

const route = useRoute()
const router = useRouter()
const {
  messageInput,
  sending,
  attachmentError,
  pendingAttachments,
  readyAttachments,
  hasAttachmentInProgress,
  isEditingMessage,
  hasComposerContext,
  showPicker,
  pickerMode,
  emojiSearch,
  gifSearch,
  attachmentInput,
  composerState,
} = useMessageComposer({
  onSendSuccess: () => {},
  onSendError: () => {},
  onAfterSend: () => {},
  scrollToBottom,
})
const {
  triggerAttachmentPicker,
  onAttachmentChange,
  queueAttachment,
  uploadAttachmentFile,
  removeAttachment,
  clearPendingAttachments,
} = useAttachments({
  selectedConversationId,
  pendingAttachments,
  attachmentError,
  attachmentInput,
  uploadAttachment,
  extractError,
})
const { messageToasts, queueToastNotification, dismissToast, openToastConversation } =
  useMessageToasts({
    router,
    selectConversation,
    ensureMessageVisible,
    generateLocalId,
  })
const { notifyNewIncomingMessage, handleIncomingNotificationPayload } = useMessageNotifications({
  selectedConversationId,
  currentUserId,
  queueToastNotification,
  openToastConversation,
  setUnreadForConversation,
  ensureMeta,
  updateConversationBlockStateByUser,
  generateLocalId,
})
const attachStream = (el, stream) => {
  if (!el) return
  if ('srcObject' in el) {
    el.srcObject = stream || null
  } else if (stream) {
    el.src = URL.createObjectURL(stream)
  } else {
    el.removeAttribute('src')
  }
  if (stream && typeof el.play === 'function') {
    el.play().catch(() => {})
  }
}
function sendCallSignal(event, payload = {}) {
  if (!socketRef.value || !selectedConversationId.value) return
  try {
    callLog('send signal', event, payload.call_id || null, payload.reason || '')
    socketRef.value.send({
      event,
      payload: {
        conversation_id: selectedConversationId.value,
        ...payload,
      },
    })
  } catch {}
}
const {
  callState,
  callControls,
  localVideoRef,
  remoteAudioRef,
  remoteVideoRef,
  remoteDisplayName,
  callStatusLabel,
  startCall,
  acceptIncomingCall,
  rejectIncomingCall,
  cancelOutgoingCall,
  hangupCall,
  toggleMicrophone,
  toggleCamera,
  handleCallSignal,
  flushPendingCandidates,
  endCall,
} = useCallControls({
  selectedConversation,
  selectedConversationId,
  currentUserId,
  displayNameForUser,
  sendCallSignal,
  notifyIncomingSummary: null,
  addLocalCallLog,
  ensurePeerConnectionReady: () => {},
  attachStream,
  generateCallId,
})
const forwardPicker = reactive({
  open: false,
  message: null,
  query: '',
})
const forwardPickerRef = ref(null)
const {
  startReply,
  startForward,
  startEdit,
  cancelComposerContext,
  initiateForward,
  cancelForwardSelection,
  confirmForwardTarget,
} = useComposerContext({
  composerState,
  messageInput,
  clearPendingAttachments,
  selectedConversationId,
  selectConversation,
  route,
  router,
  messageError,
  forwardPicker,
  resetComposerState,
})
const { deleteDialog, deleteDialogPreview, confirmDeleteMessage, closeDeleteDialog, performDeleteMessage } =
  useDeleteMessage({
    selectedConversationId,
    messagePreviewText,
    applyMessageUpdate,
    normalizeMessage,
    extractError,
  })
const { processNotificationPayload } = useNotificationsBridge({
  notificationDedupSet,
  handleIncomingNotificationPayload,
})
const pagination = reactive({
  beforeCursor: null,
  afterCursor: null,
  hasMoreBefore: false,
  hasMoreAfter: false,
})
const loadingOlderMessages = ref(false)
const suppressAutoScroll = ref(false)
const messages = ref([])

const {
  showSearchPanel,
  messageSearch,
  toggleSearchPanel,
  closeSearchPanel,
  resetSearchPanel,
  performMessageSearch,
  jumpToSearchResult,
} = useConversationSearch({
  messages,
  selectedConversationId,
  normalizeMessage,
  extractError,
  selectConversation,
  ensureMessageVisible,
  scrollToMessage,
})

const loadingMessages = ref(false)

const copiedMessageId = ref(null)

const reactionPalette = [
  '\u{1F44D}',
  '\u{2764}\u{FE0F}',
  '\u{1F389}',
  '\u{1F44F}',
  '\u{1F525}',
  '\u{1F604}',
  '\u{1F64F}',
  '\u{1F440}',
  '\u{1F680}',
  '\u{2757}',
]

const pinBusy = reactive({})

const reactionBusy = reactive({})

const reactionPickerFor = ref(null)
const messageMenuOpen = ref(null)

const gifResults = ref(gifLibrary.slice())
const loadingGifs = ref(false)
const gifError = ref('')
const gifSearchAvailable = hasGifApiSupport()
const optimisticMessageIds = new Set()
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const socketRef = ref(null)
const callLog = (...args) => {
  try {
    console.info('[call]', ...args)
  } catch {}
}
const localTypingState = reactive({ active: false, timer: null })
const LOCAL_TYPING_IDLE_MS = 3500

const connectionStatus = ref('idle')
const realtimeConversationId = ref(null)



let copyTimer = null
let gifSearchTimer = null

const messageListRef = ref(null)



const authToken = ref(localStorage.getItem('access_token') || null)
const notificationsStream = useNotificationsStream({
  token: authToken.value,
  onNotification: (payload) => processNotificationPayload(payload, 'stream'),
})


function isValidUuid(value) {
  return typeof value === 'string' && UUID_PATTERN.test(value)
}

const conversationSummary = computed(() => {

  if (loadingConversations.value) return 'Chargementâ?,?¦'

  const count = conversations.value.length

  return count ? `${count} conversation${count > 1 ? 's' : ''}` : 'Aucune conversation'

})



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


const activeFilterLabel = computed(() => {

  const option = conversationFilters.find((filter) => filter.value === conversationFilter.value)

  return option ? option.label : 'Toutes'

})


const composerBlockedInfo = computed(() => {
  const conv = selectedConversation.value
  if (!conv) return null
  if (conv.blockedByOther) {
    return {
      state: 'blocked_by_other',
      title: 'Conversation bloquée',
      message:
        `${conv.displayName || 'Ce contact'} a bloqué cette conversation. Vous ne pouvez plus répondre tant que le contact ne vous a pas débloqué.`,
    }
  }
  if (conv.blockedByMe) {
    return {
      state: 'blocked_by_me',
      title: 'Vous avez bloqué ce contact',
      message: `Débloquez ${conv.displayName || 'ce contact'} depuis la section Contacts pour reprendre l’échange.`,
    }
  }
  return null
})
const isComposerBlocked = computed(() => Boolean(composerBlockedInfo.value))

const conversationOwners = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return []
  return conv.members.filter((member) => member.role === 'owner')
})

const headerParticipants = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.participants)) return ''
  const names = conv.participants
    .map((participant) => participant.displayName || participant.email)
    .filter(Boolean)
  return names.join(', ')
})

const headerSubtitle = computed(() => {
  const parts = [headerParticipants.value, presenceSummary.value].filter(Boolean)
  return parts.join(' \u00b7 ')
})

const currentMembership = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return null
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  if (!selfId) return null
  return conv.members.find((member) => memberUserId(member) === selfId) || null
})

const isConversationOwner = computed(() => currentMembership.value?.role === 'owner')
const canManageConversation = computed(() => isConversationOwner.value)
const {
  showConversationPanel,
  conversationForm,
  savingConversation,
  conversationInfoError,
  conversationInfoNotice,
  invites,
  loadingInvites,
  inviteForm,
  inviteBusy,
  inviteRevokeBusy,
  memberBusy,
  leavingConversation,
  conversationOwnerSummary,
  roleLabel,
  clearConversationNotice,
  setConversationNotice,
  openConversationPanel,
  closeConversationPanel,
  saveConversationSettings,
  leaveCurrentConversation,
  syncConversationFormFromSelected,
  loadConversationInvites,
  submitInvite,
  revokeInvite,
  updateMemberRole,
  muteMember,
  unmuteMember,
  removeMember,
  formatInviteStatus,
} = useConversationPanel({
  selectedConversationId,
  selectedConversation,
  canManageConversation,
  conversations,
  conversationMeta,
  extractError,
  applyConversationPatch,
  applyMemberPayload,
  resetComposerState,
  clearPendingAttachments,
  resetSearchPanel,
  disconnectRealtime,
  selectConversation,
  formatAbsolute,
  conversationRoles,
})
// readyAttachments / hasAttachmentInProgress provided by useMessageComposer

const canSend = computed(() => {
  if (isComposerBlocked.value) return false
  const value = messageInput.value.trim()
  const attachmentsReady = readyAttachments.value.length > 0 && !isEditingMessage.value
  return (
    (Boolean(value) || attachmentsReady || composerState.mode === 'reply' || composerState.mode === 'forward') &&
    value.length <= 2000 &&
    Boolean(selectedConversationId.value)
  )
})


const pinnedMessages = computed(() => {
  return messages.value
    .filter((message) => message.pinned)
    .sort((a, b) => {

      const aDate = (a.pinnedAt || a.createdAt).getTime()

      const bDate = (b.pinnedAt || b.createdAt).getTime()

      return bDate - aDate

    })

})



const sortedConversations = computed(() => {

  const term = conversationSearch.value.trim().toLowerCase()

  const list = conversations.value.map((conv) => {

    const meta = conversationMeta[conv.id] || {}
    const presence = conversationPresence[conv.id] || { status: 'offline', label: STATUS_LABELS.offline }

    return {

      ...conv,

      unreadCount: meta.unreadCount || 0,

      lastPreview: meta.lastPreview || '',

      lastActivity: meta.lastActivity || conv.createdAt,

      avatarUrl: meta.avatarUrl ?? conv.avatarUrl ?? null,

      presenceStatus: presence.status,

      presenceLabel: presence.label,

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

        conv.displayName.toLowerCase().includes(term) || (conv.lastPreview || '').toLowerCase().includes(term),

    )

  }

  return filtered.sort((a, b) => new Date(b.lastActivity) - new Date(a.lastActivity))

})



const connectionStatusClass = computed(() => {

  switch (connectionStatus.value) {

    case 'connected':

      return 'ok'

    case 'connecting':

      return 'pending'

    default:

      return 'error'

  }

})



const connectionStatusLabel = computed(() => {
  switch (connectionStatus.value) {

    case 'connected':

      return 'Canal temps réel actif'

    case 'connecting':

      return 'Connexion???'

    case 'error':

      return 'Canal indisponible'

    default:

      return 'En veille'

  }

})



watch(
  () => route.query.conversation,
  (id) => {
    if (!id) return
    const convId = String(id)
    if (conversations.value.some((conv) => conv.id === convId)) {
      selectConversation(convId)
    }
  },
)

watch(
  () => forwardPicker.open,
  (open) => {
    if (open) {
      nextTick(() => {
        try {
          forwardPickerRef.value?.inputRef?.focus?.()
        } catch {}
      })
    }
  },
)

watch(authToken, (token) => {
  notificationsStream.updateToken(token || null)
  if (!token) {
    disconnectRealtime()
    return
  }
  if (selectedConversationId.value) {
    connectRealtime(selectedConversationId.value, { force: true, preservePresence: true })
  }
})

const forwardPickerTargets = computed(() => {
  const query = forwardPicker.query.trim().toLowerCase()
  return conversations.value
    .map((conv) => {
      const meta = ensureMeta(conv.id)
      const participantsLabel = (conv.participants || [])
        .map((participant) => participant.displayName || participant.email)
        .filter(Boolean)
        .join(', ')
      return {
        id: conv.id,
        displayName: conv.displayName,
        participantsLabel,
        lastActivity: meta.lastActivity || conv.createdAt || new Date(0),
      }
    })
    .filter((entry) => {
      if (!query) return true
      const haystacks = [entry.displayName, entry.participantsLabel].filter(Boolean)
      return haystacks.some((label) => label.toLowerCase().includes(query))
    })
    .sort((a, b) => {
      const tsA =
        a.lastActivity instanceof Date
          ? a.lastActivity.getTime()
          : new Date(a.lastActivity || 0).getTime()
      const tsB =
        b.lastActivity instanceof Date
          ? b.lastActivity.getTime()
          : new Date(b.lastActivity || 0).getTime()
      return tsB - tsA
    })
})

watch(selectedConversationId, (id) => {
  closeTransientMenus()
  if (forwardPicker.open) {
    cancelForwardSelection()
  }
  closeDeleteDialog()
  if (!id) {
    showConversationPanel.value = false
    invites.value = []
    clearPendingAttachments()
    resetComposerState()
    resetSearchPanel()
    return
  }
  router.replace({ query: { ...route.query, conversation: id } }).catch(() => {})
  emitActiveConversation(id)
  resetComposerState()
  resetSearchPanel()
  if (showConversationPanel.value) {
    syncConversationFormFromSelected()
    if (canManageConversation.value) {
      loadConversationInvites(id)
    } else {
      invites.value = []
    }
  }
})

watch(showConversationPanel, (open) => {
  if (open) {
    syncConversationFormFromSelected()
    if (canManageConversation.value && selectedConversationId.value) {
      loadConversationInvites(selectedConversationId.value)
    } else {
      invites.value = []
    }
  }
})

watch(canManageConversation, (canManage) => {
  if (!showConversationPanel.value) return
  if (canManage && selectedConversationId.value) {
    loadConversationInvites(selectedConversationId.value)
  } else {
    invites.value = []
  }
})

watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    if (suppressAutoScroll.value) {
      suppressAutoScroll.value = false
      return
    }
    if (!loadingOlderMessages.value) {
      scrollToBottom()
    }
  },
)

watch([showPicker, pickerMode], ([visible, mode]) => {
  if (visible && mode === 'gif') {
    loadGifResults(gifSearch.value)
  }
})

watch(gifSearch, (term) => {
  if (pickerMode.value !== 'gif' || !showPicker.value) return
  if (gifSearchTimer) clearTimeout(gifSearchTimer)
  gifSearchTimer = setTimeout(() => {
    loadGifResults(term)
  }, 350)
})


async function loadConversations() {
  loadingConversations.value = true
  conversationError.value = ''
  try {
    const { data } = await api.get('/conversations/')
    const selfId = currentUserId.value
    const list = Array.isArray(data)
      ? data.map((item) => normalizeConversation(item, { selfId })).filter(Boolean)
      : []
    conversations.value = list
    list.forEach((conv) => initializeMeta(conv))
    if (!selectedConversationId.value && list.length) {
      const initial = route.query.conversation ? String(route.query.conversation) : list[0].id
      await selectConversation(initial)
    }
    await loadUnreadSummary()

  } catch (err) {

    conversationError.value = extractError(err, "Impossible de charger les conversations.")

  } finally {

    loadingConversations.value = false

  }

}



async function loadUnreadSummary() {

  try {

    const { data } = await api.get('/messages/unread_summary')

    unreadSummary.value = {

      total: Number(data?.total || 0),

      conversations: Array.isArray(data?.conversations) ? data.conversations.map((entry) => ({

        conversation_id: String(entry.conversation_id),

        unread: Number(entry.unread || 0),

      })) : [],

    }

    applyUnreadMeta()
    emitUnreadSnapshot()

  } catch (err) {

    console.warn('Unable to load unread summary', err)

  }

}



async function loadMessages({ conversationId = selectedConversationId.value, reset = false, before = null, after = null, limit = 50 } = {}) {
  if (!conversationId) return
  if (before && after) return
  if (reset) {
    loadingMessages.value = true
    messages.value = []
    pagination.beforeCursor = null
    pagination.afterCursor = null
    pagination.hasMoreBefore = false
    pagination.hasMoreAfter = false
  }
  messageError.value = ''
  try {
    const params = { limit }
    if (before) params.before = before
    if (after) params.after = after
    const response = await api.get(`/conversations/${conversationId}/messages`, { params })
    const list = Array.isArray(response.data)
      ? response.data.map((entry) => normalizeMessage(entry, { selfId: currentUserId.value }))
      : []
    updatePaginationFromHeaders(response.headers, { reset, before, after, received: list })
    if (reset) {
      messages.value = list
    } else if (before) {
      messages.value = [...list, ...messages.value]
    } else if (after) {
      messages.value = [...messages.value, ...list]
    } else {
      messages.value = list
    }
    const meta = ensureMeta(conversationId)
    if (list.length && !before) {
      const last = list[list.length - 1]
      meta.lastPreview = last.preview
      meta.lastActivity = last.createdAt
    }
  } catch (err) {
    if (reset) {
      messageError.value = extractError(err, "Impossible de charger les messages.")
      messages.value = []
    }
  } finally {
    if (reset) {
      loadingMessages.value = false
      await nextTick()
      scrollToBottom()
    }
  }
}
async function loadOlderMessages() {
  if (
    loadingOlderMessages.value ||
    !pagination.hasMoreBefore ||
    pagination.beforeCursor == null ||
    !selectedConversationId.value
  ) {
    return
  }
  loadingOlderMessages.value = true
  suppressAutoScroll.value = true
  try {
    await loadMessages({
      conversationId: selectedConversationId.value,
      before: pagination.beforeCursor,
      limit: 50,
    })
  } finally {
    loadingOlderMessages.value = false
  }
}
const paginationHeaderKeys = {
  before: 'x-pagination-before',
  after: 'x-pagination-after',
  hasBefore: 'x-pagination-has-before',
  hasAfter: 'x-pagination-has-after',
}

function readHeader(headers, name) {
  if (!headers) return null
  if (typeof headers.get === 'function') {
    const value = headers.get(name)
    if (value != null) return value
    return headers.get(name.toLowerCase())
  }
  const lower = name.toLowerCase()
  if (lower in headers) return headers[lower]
  const exact = Object.keys(headers).find((key) => key.toLowerCase() === lower)
  return exact ? headers[exact] : null
}

function updatePaginationFromHeaders(headers, context = {}) {
  const beforeHeader = readHeader(headers, paginationHeaderKeys.before)
  const afterHeader = readHeader(headers, paginationHeaderKeys.after)
  const hasBeforeHeader = readHeader(headers, paginationHeaderKeys.hasBefore)
  const hasAfterHeader = readHeader(headers, paginationHeaderKeys.hasAfter)

  const parseNumber = (value) => {
    if (value === null || value === undefined || value === '') return null
    const num = Number(value)
    return Number.isNaN(num) ? null : num
  }

  const parseBool = (value) => {
    if (typeof value === 'boolean') return value
    if (typeof value === 'string') {
      if (value.toLowerCase() === 'true') return true
      if (value.toLowerCase() === 'false') return false
    }
    return null
  }

  const before = parseNumber(beforeHeader)
  const after = parseNumber(afterHeader)
  const hasBefore = parseBool(hasBeforeHeader)
  const hasAfter = parseBool(hasAfterHeader)

  if (context.reset) {
    pagination.beforeCursor = before
    pagination.afterCursor = after
    pagination.hasMoreBefore = hasBefore ?? false
    pagination.hasMoreAfter = hasAfter ?? false
    return
  }

  if (context.before != null) {
    pagination.beforeCursor = before
    pagination.hasMoreBefore = hasBefore ?? pagination.hasMoreBefore
  } else if (context.after != null) {
    pagination.afterCursor = after
    pagination.hasMoreAfter = hasAfter ?? pagination.hasMoreAfter
  } else if (before !== null || after !== null || hasBefore !== null || hasAfter !== null) {
    pagination.beforeCursor = before
    pagination.afterCursor = after
    if (hasBefore !== null) pagination.hasMoreBefore = hasBefore
    if (hasAfter !== null) pagination.hasMoreAfter = hasAfter
  } else if (Array.isArray(context.received)) {
    const list = context.received
    pagination.beforeCursor = list.length ? list[0].streamPosition : null
    pagination.afterCursor = list.length ? list[list.length - 1].streamPosition : null
    pagination.hasMoreBefore = Boolean(context.before && list.length)
    pagination.hasMoreAfter = Boolean(context.after && list.length)
  }
}

async function ensureMessageVisible(messageId, streamPosition) {
  if (messages.value.some((msg) => msg.id === messageId)) return

  let guard = 0

  while (

    !messages.value.some((msg) => msg.id === messageId) &&

    pagination.hasMoreBefore &&

    pagination.beforeCursor

  ) {

    if (typeof streamPosition === 'number' && pagination.beforeCursor !== null && streamPosition >= pagination.beforeCursor) {

      break

    }

    await loadOlderMessages()

    guard += 1

    if (guard > 20) break

  }
}


function applyMessageUpdate(nextMessage) {

  const idx = messages.value.findIndex((msg) => msg.id === nextMessage.id)

  if (idx === -1) {

    messages.value.push(nextMessage)

    return nextMessage

  }

  const current = messages.value[idx]

  const merged = {
    ...current,
    ...nextMessage,
    createdAt: nextMessage.createdAt || current.createdAt,
    deliveryState: nextMessage.deliveryState ?? current.deliveryState,
    deliveredAt: nextMessage.deliveredAt ?? current.deliveredAt,
    readAt: nextMessage.readAt ?? current.readAt,
    reactions: nextMessage.reactions || current.reactions,
    pinned: typeof nextMessage.pinned === 'boolean' ? nextMessage.pinned : current.pinned,
    pinnedAt: nextMessage.pinnedAt ?? current.pinnedAt,
    pinnedBy: nextMessage.pinnedBy ?? current.pinnedBy,
    security: nextMessage.security || current.security,
    preview: nextMessage.preview || current.preview,
    attachments: Array.isArray(nextMessage.attachments) ? nextMessage.attachments : current.attachments,
    editedAt: nextMessage.editedAt ?? current.editedAt,
    deletedAt: nextMessage.deletedAt ?? current.deletedAt,
    deleted: typeof nextMessage.deleted === 'boolean' ? nextMessage.deleted : current.deleted,
    replyTo: nextMessage.replyTo ?? current.replyTo,
    forwardFrom: nextMessage.forwardFrom ?? current.forwardFrom,
    streamPosition: nextMessage.streamPosition ?? current.streamPosition,
  }
  messages.value[idx] = merged

  return merged

}



function initializeMeta(conv) {

  if (!conversationMeta[conv.id]) {

    conversationMeta[conv.id] = {

      unreadCount: 0,

      lastPreview: '',

      lastActivity: conv.createdAt,

      avatarUrl: conv.avatarUrl,

    }

  }

}


function updateConversationBlockStateByUser(userId, flags = {}) {
  if (!userId) return
  const target = String(userId)
  conversations.value.forEach((conv) => {
    if (conv.type !== 'direct' || !Array.isArray(conv.members)) return
    const hasUser = conv.members.some((member) => memberUserId(member) === target)
    if (!hasUser) return
    if (Object.prototype.hasOwnProperty.call(flags, 'blockedByMe')) {
      conv.blockedByMe = Boolean(flags.blockedByMe)
    }
    if (Object.prototype.hasOwnProperty.call(flags, 'blockedByOther')) {
      conv.blockedByOther = Boolean(flags.blockedByOther)
    }
  })
}

function applyConversationBlockDetail(detail) {
  const conv = selectedConversation.value
  if (!conv || conv.type !== 'direct' || !Array.isArray(conv.members)) return
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  const other = conv.members.find((member) => memberUserId(member) !== selfId)
  const otherUserId = memberUserId(other)
  if (!other || !otherUserId) return
  updateConversationBlockStateByUser(otherUserId, {
    blockedByOther:
      Object.prototype.hasOwnProperty.call(detail || {}, 'blocked_by_other') && detail
        ? Boolean(detail.blocked_by_other)
        : undefined,
    blockedByMe:
      Object.prototype.hasOwnProperty.call(detail || {}, 'blocked_by_you') && detail
        ? Boolean(detail.blocked_by_you)
        : undefined,
  })
}



function ensureMeta(convId) {

  initializeMeta({ id: convId, createdAt: new Date(), avatarUrl: null })

  return conversationMeta[convId]

}



function applyUnreadMeta() {

  const map = new Map(unreadSummary.value.conversations.map((entry) => [String(entry.conversation_id), Number(entry.unread || 0)]))

  conversations.value.forEach((conv) => {

    const meta = ensureMeta(conv.id)

    meta.unreadCount = map.get(conv.id) || 0

  })

}



async function selectConversation(convId) {
  const id = String(convId)
  if (!conversations.value.some((conv) => conv.id === id)) return
  const isSame = selectedConversationId.value === id
  selectedConversationId.value = id
  messageInput.value = ''
  showPicker.value = false
  emojiSearch.value = ''
  gifSearch.value = ''
  gifError.value = ''
  loadingGifs.value = false
  gifResults.value = gifLibrary.slice()
  pickerMode.value = 'emoji'
  clearPendingAttachments()
  resetComposerState()
  endCall(true)
  resetPresenceState()
  stopLocalTyping()
  messages.value = []
  disconnectRealtime()
  await loadMessages({ conversationId: id, reset: true })
  connectRealtime(id)
  await markConversationAsRead(id)
  if (!isSame) {
    await loadUnreadSummary()
  }
}

function emitUnreadSnapshot() {
  if (typeof window === 'undefined') return
  try {
    const byConversation = unreadSummary.value.conversations.reduce((acc, entry) => {
      acc[entry.conversation_id] = entry.unread
      return acc
    }, {})
    const payload = {
      total: unreadSummary.value.total,
      by_conversation: byConversation,
    }
    window.dispatchEvent(new CustomEvent('cova:unread', { detail: payload }))
    localStorage.setItem('unread_counts', JSON.stringify(byConversation))
  } catch {}
}

function setUnreadForConversation(convId, newCount) {
  const entries = unreadSummary.value.conversations.slice()
  const idx = entries.findIndex((entry) => entry.conversation_id === convId)
  const previous = idx >= 0 ? Number(entries[idx].unread || 0) : 0
  if (newCount > 0) {
    const normalized = { conversation_id: convId, unread: newCount }
    if (idx >= 0) entries[idx] = normalized
    else entries.push(normalized)
  } else if (idx >= 0) {
    entries.splice(idx, 1)
  }
  const total = Math.max(unreadSummary.value.total - previous + Math.max(newCount, 0), 0)
  unreadSummary.value = {
    total,
    conversations: entries,
  }
  emitUnreadSnapshot()
}

async function markConversationAsRead(convId, ids = []) {
  if (!convId) return
const meta = ensureMeta(convId)
const uniqueIds = Array.isArray(ids) ? Array.from(new Set(ids.filter(Boolean))) : []
if (uniqueIds.length) {
  const decrement = Math.min(uniqueIds.length, meta.unreadCount || 0)
  meta.unreadCount = Math.max((meta.unreadCount || 0) - decrement, 0)
  setUnreadForConversation(convId, meta.unreadCount)
} else {
  meta.unreadCount = 0
  setUnreadForConversation(convId, 0)
}
  const body = uniqueIds.length ? { message_ids: uniqueIds } : {}
  applyLocalReadReceipt(convId, uniqueIds)
  try {
    await api.post(`/conversations/${convId}/read`, body)
  } catch (err) {
    console.warn('Unable to synchroniser la lecture', err)
  }
}

function applyLocalReadReceipt(convId, ids = []) {
  const targetIds =
    Array.isArray(ids) && ids.length ? new Set(ids.map((id) => String(id))) : null
  const now = new Date()
  messages.value.forEach((message) => {
    if (String(message.conversationId) !== String(convId)) return
    if (message.sentByMe || message.deleted) return
    if (targetIds && !targetIds.has(String(message.id))) return
    if (message.deliveryState === 'read') return
    message.deliveryState = 'read'
    message.readAt = now
  })
}



function incrementUnreadCounter(convId) {
  const meta = ensureMeta(convId)
  meta.unreadCount = (meta.unreadCount || 0) + 1
  setUnreadForConversation(convId, meta.unreadCount)
}

function applyConversationPatch(payload) {
  if (!payload) return
  const normalized = normalizeConversation(payload, { selfId: currentUserId.value })
  if (!normalized) return
  const idx = conversations.value.findIndex((conv) => conv.id === normalized.id)
  if (idx >= 0) {
    conversations.value[idx] = { ...conversations.value[idx], ...normalized }
  } else {
    conversations.value.push(normalized)
    initializeMeta(normalized)
  }
}

function applyMemberPayload(payload) {
  const normalized = normalizeMember(payload)
  if (!normalized) return
  const convId = selectedConversationId.value
  if (!convId) return
  const target = conversations.value.find((conv) => conv.id === convId)
  if (!target) return
  if (!Array.isArray(target.members)) {
    target.members = []
  }
  const idx = target.members.findIndex((member) => member.id === normalized.id)
  if (idx >= 0) {
    target.members[idx] = normalized
  } else {
    target.members.push(normalized)
  }
  const activeMembers = target.members.filter((member) => member.state === 'active')
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  target.participants = activeMembers.filter((member) => !selfId || memberUserId(member) !== selfId)
}

async function loadGifResults(query = '') {
  if (!showPicker.value || pickerMode.value !== 'gif') {
    return
  }
  if (!gifSearchAvailable) {
    gifResults.value = gifLibrary
    gifError.value = ''
    return
  }
  loadingGifs.value = true
  gifError.value = ''
  try {
    const gifs = await fetchGifs({ query, limit: 30 })
    gifResults.value = gifs.length ? gifs : gifLibrary
  } catch (error) {
    gifResults.value = gifLibrary
    gifError.value = "Impossible de charger les GIFs."
  } finally {
    loadingGifs.value = false
  }
}


function onComposerInput() {
  limitDraft()
  handleTypingActivity()
}

function handleTypingActivity() {
  if (!selectedConversationId.value || !socketRef.value) {
    stopLocalTyping()
    return
  }
  if (!messageInput.value.trim()) {
    stopLocalTyping()
    return
  }
  if (!localTypingState.active) {
    try {
      socketRef.value.send({ event: 'typing:start' })
    } catch {}
    localTypingState.active = true
  }
  if (localTypingState.timer) {
    clearTimeout(localTypingState.timer)
  }
  localTypingState.timer = setTimeout(() => stopLocalTyping(), LOCAL_TYPING_IDLE_MS)
}

function handleComposerBlur() {
  stopLocalTyping()
}

function stopLocalTyping() {
  if (localTypingState.timer) {
    clearTimeout(localTypingState.timer)
    localTypingState.timer = null
  }
  if (!localTypingState.active || !socketRef.value) {
    localTypingState.active = false
    return
  }
  try {
    socketRef.value.send({ event: 'typing:stop' })
  } catch {}
  localTypingState.active = false
}

function limitDraft() {

  if (messageInput.value.length > 2000) {

    messageInput.value = messageInput.value.slice(0, 2000)

  }

}



async function sendMessage() {
  if (!selectedConversationId.value || !canSend.value) return
  if (composerState.mode === 'edit' && composerState.targetMessageId) {
    await submitMessageEdit()
    return
  }
  if (hasAttachmentInProgress.value) {
    attachmentError.value = 'Sélectionnez une conversation avant d\'ajouter un fichier.'
    return
  }
  if (pendingAttachments.value.some((entry) => entry.status === 'error')) {
    attachmentError.value = 'Retirez ou renvoyez les fichiers en erreur avant l\'envoi.'
    return
  }
  attachmentError.value = ''
  const readyList = pendingAttachments.value.filter((entry) => entry.status === 'ready')
  const attachmentsPayload = readyList
    .map((entry) => entry.descriptor?.upload_token)
    .filter(Boolean)
    .map((token) => ({ upload_token: token }))
  const draftContent = messageInput.value.trim()
  const forwardSameConversation =
    composerState.forwardFrom &&
    composerState.forwardFrom.conversationId &&
    selectedConversationId.value &&
    String(composerState.forwardFrom.conversationId) === String(selectedConversationId.value)
  const replyToId =
    composerState.replyTo && isValidUuid(composerState.replyTo.id) ? composerState.replyTo.id : null
  const forwardId =
    composerState.forwardFrom && forwardSameConversation && isValidUuid(composerState.forwardFrom.id)
      ? composerState.forwardFrom.id
      : null
  const payload = {
    content: draftContent,
    attachments: attachmentsPayload,
    reply_to_message_id: replyToId,
    forward_message_id: forwardId,
  }
  const optimisticId = generateLocalId()
  const optimisticMessage = {
    id: optimisticId,
    conversationId: selectedConversationId.value,
    content: draftContent,
    preview: draftContent.slice(0, 120),
    displayName: 'Vous',
    sentByMe: true,
    createdAt: new Date(),
    deliveryState: 'queued',
    reactions: [],
    pinned: false,
    pinnedAt: null,
    pinnedBy: null,
    isSystem: false,
    deleted: false,
    attachments: mapOptimisticAttachments(readyList),
    replyTo: cloneComposerReference(composerState.replyTo),
    forwardFrom: forwardSameConversation ? cloneComposerReference(composerState.forwardFrom) : null,
    localOnly: true,
  }
  messages.value.push(optimisticMessage)
  optimisticMessageIds.add(optimisticId)
  const previousInputValue = messageInput.value
  messageInput.value = ''
  await nextTick()
  scrollToBottom()
  sending.value = true
  try {
    const { data } = await api.post(`/conversations/${selectedConversationId.value}/messages`, payload)
    const message = normalizeMessage(data, { selfId: currentUserId.value })
    message.sentByMe = true
    resolveOptimisticMessage(optimisticId, message)
    showPicker.value = false
    emojiSearch.value = ''
    gifSearch.value = ''
    gifError.value = ''
    loadingGifs.value = false
    gifResults.value = gifLibrary.slice()
    pickerMode.value = 'emoji'
    clearPendingAttachments()
    resetComposerState()
    const meta = ensureMeta(selectedConversationId.value)
    meta.lastPreview = message.preview
    meta.lastActivity = message.createdAt
    meta.unreadCount = 0
    await loadUnreadSummary()
  } catch (err) {
    optimisticMessageIds.delete(optimisticId)
    removeMessageById(optimisticId)
    messageInput.value = previousInputValue
    const detail = err?.response?.data?.detail || err?.response?.data
    if (detail && typeof detail === 'object' && detail.code === 'conversation_blocked') {
      applyConversationBlockDetail(detail)
      messageError.value =
        detail.reason === 'blocked_by_other'
          ? 'Ce contact a bloqué cette conversation.'
          : 'Vous avez bloqué cette conversation.'
    } else {
      messageError.value = extractError(err, "Impossible d'envoyer le message.")
    }
  } finally {
    sending.value = false
    stopLocalTyping()
  }
}

async function submitMessageEdit() {
  if (
    !selectedConversationId.value ||
    !composerState.targetMessageId ||
    !isValidUuid(composerState.targetMessageId)
  ) {
    return
  }
  sending.value = true
  try {
    const data = await editConversationMessage(selectedConversationId.value, composerState.targetMessageId, {
      content: messageInput.value.trim(),
    })
    const message = normalizeMessage(data, { selfId: currentUserId.value })
    message.sentByMe = true
    applyMessageUpdate(message)
    messageInput.value = ''
    resetComposerState()
    showPicker.value = false
  } catch (err) {
    messageError.value = extractError(err, 'Impossible de modifier le message.')
  } finally {
    sending.value = false
    stopLocalTyping()
  }
}


function connectRealtime(convId, options = {}) {
  const targetId = convId ? String(convId) : null
  if (!targetId) {
    disconnectRealtime()
    return
  }
  if (!authToken.value) {
    disconnectRealtime()
    return
  }
  const { force = false, preservePresence = false } = options
  const sameConversation = realtimeConversationId.value === targetId
  if (!force && sameConversation && socketRef.value) {
    return
  }
  if (socketRef.value) {
    disconnectRealtime({
      preserveConversation: sameConversation,
      preservePresence: preservePresence && sameConversation,
    })
  }
  connectionStatus.value = 'connecting'
  realtimeConversationId.value = targetId
  socketRef.value = createConversationSocket(targetId, {
    token: authToken.value,
    onOpen: () => {
      connectionStatus.value = 'connected'
    },
    onError: () => {
      connectionStatus.value = 'error'
    },
    onClose: () => {
      connectionStatus.value = 'idle'
    },
    onEvent: (payload) => {
      if (!payload || typeof payload !== 'object') return
      switch (payload.event) {
        case 'ready':
          connectionStatus.value = 'connected'
          return
        case 'message':
        case 'message.updated':
          handleIncomingRealtime(payload)
          return
        case 'typing:start':
        case 'typing:stop':
          handleRealtimeTyping(payload)
          return
        case 'presence:update':
          applyPresencePayload(payload.payload)
          return
        case 'call:offer':
        case 'call:answer':
        case 'call:candidate':
        case 'call:hangup':
          handleRealtimeCallEvent(payload)
          return
        default:
          break
      }
    },
  })
}



function disconnectRealtime(options = {}) {
  const { preserveConversation = false, preservePresence = false } = options
  if (socketRef.value) {
    try {
      socketRef.value.close()
    } catch {}
    socketRef.value = null
  }
  connectionStatus.value = 'idle'
  stopLocalTyping()
  if (!preservePresence) {
    resetPresenceState()
  }
  if (!preserveConversation) {
    realtimeConversationId.value = null
  }
}

function handleIncomingRealtime(payload) {
  const type = typeof payload?.event === 'string' ? payload.event : 'message'
  const message = normalizeMessage(payload, { selfId: currentUserId.value })
  const meta = ensureMeta(message.conversationId)
  if (typeof message.streamPosition === 'number') {
    pagination.afterCursor = pagination.afterCursor
      ? Math.max(pagination.afterCursor, message.streamPosition)
      : message.streamPosition
  }
  if (type === 'message') {
    meta.lastPreview = message.preview
    meta.lastActivity = message.createdAt
  }
  const isSameConversation = message.conversationId === selectedConversationId.value
  const shouldNotify = type === 'message' && !message.sentByMe && !message.isSystem && !message.deleted
  if (isSameConversation) {
    applyMessageUpdate(message)
    if (shouldNotify) {
      markConversationAsRead(message.conversationId, [message.id]).catch(() => {})
    }
  } else if (shouldNotify) {
    incrementUnreadCounter(message.conversationId)
  }
  if (
    shouldNotify &&
    (!isSameConversation || (typeof document !== 'undefined' && (document.hidden || !document.hasFocus())))
  ) {
    notifyNewIncomingMessage(message)
  }
}

function scrollToBottom() {
  messageListRef.value?.scrollToBottom?.()
}


function onAvatarFailure(convId) {

  const meta = ensureMeta(convId)

  meta.avatarUrl = null

}



function emitActiveConversation(convId) {

  window.dispatchEvent(new CustomEvent('cova:active-conversation', { detail: { convId } }))

}



function goToNewConversation() {

  router.push({ path: '/dashboard/messages/new' }).catch(() => {})

}




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

function addEmoji(emoji) {
  if (!emoji) return
  const separator = messageInput.value && !messageInput.value.endsWith(' ') ? ' ' : ''
  messageInput.value = `${messageInput.value || ''}${separator}${emoji} `
  showPicker.value = false
  emojiSearch.value = ''
  gifSearch.value = ''
  limitDraft()
  handleTypingActivity()
}

function insertGif(gif) {
  if (!gif?.url) return
  const base = messageInput.value ? `${messageInput.value.trim()} ` : ''
  messageInput.value = `${base}${gif.url} `
  showPicker.value = false
  gifSearch.value = ''
  gifError.value = ''
  limitDraft()
  handleTypingActivity()
}




function generateCallId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `call_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function handleRealtimeCallEvent(payload) {
  handleCallSignal(payload)
}

function addLocalCallLog(summary) {
  const direction = summary.initiator ? 'sortant' : 'entrant'
  const kindLabel = summary.kind === 'video' ? 'vidéo' : 'audio'
  const outcomeMap = {
    hangup: 'terminé',
    decline: 'refusé',
    canceled: 'annulé',
    busy: 'occupé',
    failed: 'interrompu',
    ended: 'terminé',
  }
  const outcome = outcomeMap[summary.reason] || 'terminé'
  const content = `Appel ${kindLabel} ${direction} ${outcome} - ${summary.remote || 'participant'}`
  messages.value.push({
    id: generateLocalId(),
    conversationId: selectedConversationId.value,
    authorId: null,
    displayName: 'Système',
    avatarUrl: null,
    content,
    createdAt: new Date(),
    isSystem: true,
    sentByMe: false,
    deliveryState: 'delivered',
    localOnly: true,
  })
}


async function copyMessage(message) {

  if (!message?.content) return

  try {

    if (navigator?.clipboard?.writeText) {

      await navigator.clipboard.writeText(message.content)

      copiedMessageId.value = message.id

      if (copyTimer) clearTimeout(copyTimer)

      copyTimer = setTimeout(() => {

        copiedMessageId.value = null

        copyTimer = null

      }, 1500)

    }

  } catch (err) {

    console.warn('Impossible de copier le message', err)

  }

}





function cloneComposerReference(target) {
  if (!target) return null
  return {
    id: target.id,
    displayName: target.displayName,
    authorDisplayName: target.authorDisplayName || target.displayName || target.email || 'Participant',
    excerpt: target.excerpt || messagePreviewText(target),
    deleted: Boolean(target.deleted),
  }
}



function mapOptimisticAttachments(entries) {
  return entries.map((entry) => ({
    id: entry.descriptor?.id || entry.id,
    fileName: entry.name || entry.descriptor?.file_name || 'Pièce jointe',
    mimeType: entry.type || entry.descriptor?.mime_type || 'Fichier',
    sizeBytes: entry.size,
    downloadUrl: entry.descriptor?.download_url || null,
  }))
}



function removeMessageById(messageId) {
  const idx = messages.value.findIndex((msg) => msg.id === messageId)
  if (idx !== -1) {
    messages.value.splice(idx, 1)
  }
}



function resolveOptimisticMessage(localId, nextMessage) {
  optimisticMessageIds.delete(localId)
  removeMessageById(localId)
  applyMessageUpdate(nextMessage)
}



function isPinning(messageId) {
  return Boolean(pinBusy[messageId])
}


function isReactionPending(messageId, emoji) {
  return Boolean(reactionBusy[`${messageId}:${emoji}`])
}



function toggleReactionPicker(messageId) {
  if (!messageId) return
  reactionPickerFor.value = reactionPickerFor.value === messageId ? null : messageId
  if (reactionPickerFor.value) {
    messageMenuOpen.value = null
  }
}



function toggleMessageMenu(messageId) {
  if (!messageId) return
  messageMenuOpen.value = messageMenuOpen.value === messageId ? null : messageId
  if (messageMenuOpen.value) {
    reactionPickerFor.value = null
  }
}



function closeTransientMenus() {
  reactionPickerFor.value = null
  messageMenuOpen.value = null
}



async function handlePinToggle(message) {
  await togglePin(message)
  closeTransientMenus()
}



async function handleReactionSelection(message, emoji) {
  await toggleReaction(message, emoji)
  reactionPickerFor.value = null
}



async function togglePin(message) {

  if (!selectedConversationId.value) return

  const messageId = message.id

  pinBusy[messageId] = true

  try {

    const data = message.pinned

      ? await unpinMessage(selectedConversationId.value, messageId)

      : await pinMessage(selectedConversationId.value, messageId)

    applyMessageUpdate(normalizeMessage(data, { selfId: currentUserId.value }))

  } catch (err) {

    messageError.value = extractError(err, "Impossible de mettre à jour l'épingle.")

  } finally {

    pinBusy[messageId] = false

  }

}



async function toggleReaction(message, emoji) {

  if (!selectedConversationId.value || !emoji) return

  const key = `${message.id}:${emoji}`

  reactionBusy[key] = true

  try {

    const data = await updateMessageReaction(selectedConversationId.value, message.id, { emoji })

    applyMessageUpdate(normalizeMessage(data, { selfId: currentUserId.value }))

  } catch (err) {

    console.warn('Impossible de mettre à jour la réaction', err)

  } finally {

    reactionBusy[key] = false

  }

}


function downloadAttachment(attachment) {
  if (!attachment || !attachment.downloadUrl) return
  window.open(attachment.downloadUrl, '_blank', 'noopener')
}


const messageFormatters = createMessageFormatters({
  formatTime,
  formatAbsolute,
  formatFileSize,
  extractDeliverySummary,
})




function scrollToMessage(messageId) {
  if (messageListRef.value?.scrollToMessage) {
    messageListRef.value.scrollToMessage(messageId)
    return
  }
  const el = document.getElementById(`message-${messageId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('msg-bubble--focus')
    setTimeout(() => {
      el.classList.remove('msg-bubble--focus')
    }, 1200)
  }
}

function extractError(err, fallback) {
  if (!err) return fallback
  if (typeof err === 'string') return err
  const data = err.response?.data
  const detail =
    (typeof data?.detail === 'string' && data.detail) ||
    (Array.isArray(data?.detail) && data.detail.length && data.detail[0]) ||
    data?.message ||
    data?.error ||
    err.message
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  return fallback
}

function handleGlobalNotificationEvent(event) {
  const payload = event?.detail
  if (!payload) return
  processNotificationPayload(payload, payload.__origin || 'bridge')
}

async function handleExternalConversationRequest(event) {
  const targetId = event?.detail?.id
  if (!targetId) return
  await selectConversation(String(targetId))
  const messageId = event.detail?.messageId
  if (messageId) {
    await nextTick()
    await ensureMessageVisible(messageId)
  }
}

function handleDocumentClick() {
  if (forwardPicker.open) {
    cancelForwardSelection()
    return
  }
  if (!reactionPickerFor.value && !messageMenuOpen.value) return
  closeTransientMenus()
}



function handleDocumentKeydown(event) {
  if (event.key !== 'Escape') return
  if (forwardPicker.open) {
    event.preventDefault()
    cancelForwardSelection()
    return
  }
  if (!reactionPickerFor.value && !messageMenuOpen.value) return
  event.preventDefault()
  closeTransientMenus()
}



watch(
  () => composerBlockedInfo.value?.state,
  (state, previous) => {
    if (state && state !== previous) {
      messageInput.value = ''
      clearPendingAttachments()
      resetComposerState()
    }
  },
)

onMounted(async () => {
  await loadConversations()
  await loadAvailabilityStatus()
  if (typeof window !== 'undefined') {
    document.addEventListener('click', handleDocumentClick)
    document.addEventListener('keydown', handleDocumentKeydown)
    window.addEventListener('cova:profile-update', handleProfileBroadcast)
    window.addEventListener('cova:notification-event', handleGlobalNotificationEvent)
    window.addEventListener('cova:open-conversation', handleExternalConversationRequest)
  }
  typingCleanupTimer = setInterval(cleanupRemoteTyping, 2000)
})


onBeforeUnmount(() => {
  endCall(true)
  disconnectRealtime()
  if (gifSearchTimer) {
    clearTimeout(gifSearchTimer)
  }
  if (typingCleanupTimer) {
    clearInterval(typingCleanupTimer)
    typingCleanupTimer = null
  }
  if (typeof window !== 'undefined') {
    document.removeEventListener('click', handleDocumentClick)
    document.removeEventListener('keydown', handleDocumentKeydown)
    window.removeEventListener('cova:profile-update', handleProfileBroadcast)
    window.removeEventListener('cova:notification-event', handleGlobalNotificationEvent)
    window.removeEventListener('cova:open-conversation', handleExternalConversationRequest)
  }
})
</script>

<style src="@/assets/styles/messages.css"></style>






































