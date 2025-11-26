<!--
===== Vue Overview : MessagesView =====
- Role: tableau de bord complet des conversations avec gestion temps reel.
- Architecture: assemble la sidebar, la zone principale, les panneaux et pickers relies aux composables messages.
- Flux: combine etats locaux, websocket et appels API pour synchroniser messages, presence, appels et toasts.
- Maintenance: chaque section du template correspond a un sous-composant specialise pour limiter le couplage.
-->
<!--`n############################################################`n# Vue : MessagesView`n# Auteur : Valentin Masurelle`n# Date   : 2025-05-04`n# Description:`n# - Page principale de messagerie avec sidebar, liste de messages et editeur.`n# - Orchestration des composants de conversation, toasts et fichiers attaches.`n############################################################`n-->
<template>

  <!-- Layout racine: shell principal avec toasts et colonnes -->
  <div class="msg-shell">
    <!-- Pile de toasts pour notifier les evenements conversation -->
    <MessageToastStack
      :toasts="messageToasts"
      :formatter="formatTime"
      @dismiss="dismissToast"
      @open="openToastConversation"
    />

    <!-- Grille principale: sidebar de navigation + contenu conversation -->
    <div class="msg-layout">

      <!-- Sidebar: liste des conversations, filtres et actions de creation -->
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

      <!-- Zone principale: header conversation, recherche, liste et editeur -->
      <section class="msg-main">

        <!-- Etat vide: invite a creer ou selectionner une conversation -->
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
        <!-- Liste des messages (pagination, reactions, pins) -->
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

        <!-- Editeur principal: texte, emoji, gifs, pieces jointes -->
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
          :on-gif-search="(value) => { gifSearch.value = value || '' }"
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

        <!-- Modale de confirmation pour suppression de message -->
        <DeleteMessageModal
          v-model:visible="deleteDialog.visible"
          :preview="deleteDialogPreview"
          :error="deleteDialog.error"
          :loading="deleteDialog.loading"
          @close="closeDeleteDialog"
          @confirm="performDeleteMessage"
        />

        <!-- Overlay d'appel audio/visio pour les interactions temps reel -->
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
  <!-- Panneau lateral: informations conversation et gestion membres -->
  <ConversationPanel
    :show="showConversationPanel"
    :selected-conversation="selectedConversation"
    :conversation-owner-summary="conversationOwnerSummary"
    :conversation-info-error="conversationInfoError"
    :conversation-info-notice="conversationInfoNotice"
    :conversation-form="conversationForm"
    :saving-conversation="savingConversation"
    :leaving-conversation="leavingConversation"
    :deleting-conversation="deletingConversation"
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
    :open-delete-confirm="openDeleteConfirm"
    :close-delete-confirm="closeDeleteConfirm"
    :delete-current-conversation="deleteCurrentConversation"
    :submit-invite="submitInvite"
    :revoke-invite="revokeInvite"
    :update-member-role="updateMemberRole"
    :mute-member="muteMember"
    :unmute-member="unmuteMember"
    :remove-member="removeMember"
  />


  <!-- Selection de cible pour le transfert de message -->
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

// ===== Imports UI et composables messages =====
import { computed, reactive, ref } from 'vue'

import { useRoute, useRouter } from 'vue-router'
import { useConversationSearch } from '@/composables/useConversationSearch'
import { uploadAttachment } from '@/services/conversations'
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
import { useMessageComposer } from '@/composables/useMessageComposer'
import { STATUS_LABELS, availabilityOptions } from '@/modules/messages/constants'
import {
  formatTime,
  formatAbsolute,
  formatFileSize,
  messagePreviewText,
  extractDeliverySummary,
} from '@/modules/messages/formatters'
import { useAttachments } from '@/modules/messages/useAttachments'
import { useMessageToasts } from '@/modules/messages/useMessageToasts'
import { useCallControls } from '@/modules/messages/useCallControls'
import { generateLocalId } from '@/modules/messages/id'
import { useNotificationsBridge } from '@/modules/messages/useNotificationsBridge'
import { useMessageNotifications } from '@/modules/messages/useMessageNotifications'
import { useConversationPanel } from '@/modules/messages/useConversationPanel'
import { useComposerContext } from '@/modules/messages/useComposerContext'
import { useDeleteMessage } from '@/modules/messages/useDeleteMessage'
import { useConversationsState } from '@/modules/messages/useConversationsState'
import { memberUserId, normalizeMessage } from '@/modules/messages/mappers'
import { usePresenceStatus } from '@/modules/messages/usePresenceStatus'
import { useConversationFilters } from '@/modules/messages/useConversationFilters'
import { useMessageActions } from '@/modules/messages/useMessageActions'
import { useMessageList } from '@/modules/messages/useMessageList'
import { useComposerInteractions } from '@/modules/messages/useComposerInteractions'
import { useConversationRealtime } from '@/modules/messages/useConversationRealtime'
import { useMessagesLifecycle } from '@/modules/messages/useMessagesLifecycle'

// ===== Etats globaux et navigation =====
const selectedConversationId = ref(null)
const currentUserId = ref(localStorage.getItem('user_id') || null)
const notificationDedupSet = new Set()
const messageError = ref('')
const route = useRoute()
const router = useRouter()
const messageReadBridge = { applyLocalReadReceipt: null }

const {
  conversations,
  conversationMeta,
  loadingConversations,
  conversationError,
  unreadSummary,
  ensureMeta,
  loadConversations,
  loadUnreadSummary,
  setUnreadForConversation,
  markConversationAsRead,
  incrementUnreadCounter,
  applyConversationPatch,
  applyMemberPayload,
  updateConversationBlockStateByUser,
  onAvatarFailure,
} = useConversationsState({
  route,
  selectConversation,
  currentUserId,
  selectedConversationId,
  applyLocalReadReceipt: (...args) => messageReadBridge.applyLocalReadReceipt?.(...args),
  extractError,
})

// ----- Conversation selectionnee et helpers derives -----
const selectedConversation = computed(() => {
  if (!selectedConversationId.value) return null
  return conversations.value.find((conv) => conv.id === selectedConversationId.value) || null
})

// ----- Utilitaires d'etat: conversation muette, presence membre -----
const isConversationMuted = (convId) => {
  const id = convId ? String(convId) : null
  if (!id || !currentUserId.value) return false
  const conv = conversations.value.find((item) => item.id === id)
  if (!conv || !Array.isArray(conv.members)) return false
  const self = String(currentUserId.value)
  const me = conv.members.find((member) => memberUserId(member) === self || String(member.userId || member.id) === self)
  if (!me || !me.mutedUntil) return false
  return me.mutedUntil.getTime() > Date.now()
}

// ===== Presence et statut temps reel =====
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

// ===== Filtres et tri des conversations =====
const {
  conversationSearch,
  conversationFilter,
  conversationFilters,
  conversationRoles,
  conversationSummary,
  sortedConversations,
} = useConversationFilters({
  conversations,
  conversationMeta,
  loadingConversations,
  conversationPresence,
  defaultPresenceLabel: STATUS_LABELS.offline,
})

// ===== Composer: message, pieces jointes et contextes =====
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
// ----- Gestion des pieces jointes (file picker + upload) -----
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
// ===== Liste des messages et pagination =====
const {
  messages,
  pagination,
  loadingMessages,
  loadingOlderMessages,
  suppressAutoScroll,
  loadMessages,
  loadOlderMessages,
  ensureMessageVisible,
  applyMessageUpdate,
  applyLocalReadReceipt,
} = useMessageList({
  selectedConversationId,
  currentUserId,
  ensureMeta,
  extractError,
  scrollToBottom,
  messageError,
})
messageReadBridge.applyLocalReadReceipt = applyLocalReadReceipt
// ----- Toasts de nouveaux messages et navigation rapide -----
const { messageToasts, queueToastNotification, dismissToast, openToastConversation } =
  useMessageToasts({
    router,
    selectConversation,
    ensureMessageVisible,
    generateLocalId,
  })
// ----- Notifications push + deduplication -----
const { notifyNewIncomingMessage, handleIncomingNotificationPayload } = useMessageNotifications({
  selectedConversationId,
  currentUserId,
  queueToastNotification,
  openToastConversation,
  setUnreadForConversation,
  ensureMeta,
  updateConversationBlockStateByUser,
  generateLocalId,
  isConversationMuted,
})
// ----- Utilitaires media: attache flux audio/video aux balises -----
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
// ===== Transfert de message: etat du picker =====
const forwardPicker = reactive({
  open: false,
  message: null,
  query: '',
})
const forwardPickerRef = ref(null)
// ----- Gestion du contexte (reponse, transfert, edition) -----
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
// ----- Modale de suppression et callbacks -----
const { deleteDialog, deleteDialogPreview, confirmDeleteMessage, closeDeleteDialog, performDeleteMessage } =
  useDeleteMessage({
    selectedConversationId,
    messagePreviewText,
    applyMessageUpdate,
  normalizeMessage,
  extractError,
})
// ----- Passerelle notifications navigateur -> etat local -----
const { processNotificationPayload } = useNotificationsBridge({
  notificationDedupSet,
  handleIncomingNotificationPayload,
})
// ===== Canal temps reel (WebSocket) pour messages/presence/appels =====
const {
  socketRef,
  connectionStatus,
  realtimeConversationId,
  sendCallSignal,
  connectRealtime,
  disconnectRealtime,
  setCallEventHandler,
  setStopLocalTyping,
} = useConversationRealtime({
  selectedConversationId,
  currentUserId,
  normalizeMessage,
  ensureMeta,
  pagination,
  applyMessageUpdate,
  markConversationAsRead,
  incrementUnreadCounter,
  notifyNewIncomingMessage,
  handleRealtimeTyping,
  applyPresencePayload,
  resetPresenceState,
  processNotificationPayload,
  isConversationMuted,
})
// ===== Appels audio/visio: controle et affichage =====
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
setCallEventHandler(handleCallSignal)

// ===== Recherche plein texte dans une conversation =====
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

// ===== Actions sur messages (reactions, pins, copie, telechargements) =====
const {
  cloneComposerReference,
  mapOptimisticAttachments,
  removeMessageById,
  resolveOptimisticMessage,
  reactionPickerFor,
  messageMenuOpen,
  toggleReactionPicker,
  toggleMessageMenu,
  closeTransientMenus,
  handlePinToggle,
  handleReactionSelection,
  togglePin,
  toggleReaction,
  isPinning,
  isReactionPending,
  optimisticMessageIds,
  copyMessage,
  copiedMessageId,
  downloadAttachment,
  messageFormatters,
} = useMessageActions({
  messages,
  selectedConversationId,
  currentUserId,
  messageError,
  applyMessageUpdate,
  normalizeMessage,
  extractError,
  messagePreviewText,
  formatTime,
  formatAbsolute,
  formatFileSize,
  extractDeliverySummary,
})

// Palette d'emoji par defaut pour les reactions rapides
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

// Reference DOM de la liste pour le scroll et le focus
const messageListRef = ref(null)
// ===== Interactions du composer (emoji, gif, saisie, envoi) =====
const {
  filteredEmojiSections,
  displayedGifs,
  gifError,
  loadingGifs,
  gifSearchAvailable,
  composerBlockedInfo,
  isComposerBlocked,
  canSend,
  togglePicker,
  setPickerMode,
  resetPickerState,
  addEmoji,
  insertGif,
  onComposerInput,
  handleComposerBlur,
  stopLocalTyping,
  sendMessage,
  submitMessageEdit,
} = useComposerInteractions({
  messageInput,
  composerState,
  showPicker,
  pickerMode,
  emojiSearch,
  gifSearch,
  pendingAttachments,
  readyAttachments,
  hasAttachmentInProgress,
  isEditingMessage,
  selectedConversation,
  selectedConversationId,
  currentUserId,
  attachmentError,
  messages,
  messageError,
  mapOptimisticAttachments,
  cloneComposerReference,
  resolveOptimisticMessage,
  optimisticMessageIds,
  removeMessageById,
  clearPendingAttachments,
  resetComposerState,
  ensureMeta,
  loadUnreadSummary,
  normalizeMessage,
  extractError,
  updateConversationBlockStateByUser,
  memberUserId,
  applyMessageUpdate,
  scrollToBottom,
  socketRef,
  generateLocalId,
  sending,
})
setStopLocalTyping(stopLocalTyping)

// ----- Informations derivees pour droits et affichage d'entete -----
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
// ===== Panneau d'information conversation (roles, invites, moderation) =====
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
  deletingConversation,
  showDeleteConfirm,
  conversationOwnerSummary,
  roleLabel,
  clearConversationNotice,
  setConversationNotice,
  openConversationPanel,
  closeConversationPanel,
  saveConversationSettings,
  leaveCurrentConversation,
  openDeleteConfirm,
  closeDeleteConfirm,
  deleteCurrentConversation,
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


// ----- Messages epingles affiches en haut de la liste -----
const pinnedMessages = computed(() => {
  return messages.value
    .filter((message) => message.pinned)
    .sort((a, b) => {

      const aDate = (a.pinnedAt || a.createdAt).getTime()

      const bDate = (b.pinnedAt || b.createdAt).getTime()

      return bDate - aDate

    })

})



// ----- Etiquettes de statut de connexion temps reel -----
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


// ===== Gestion du cycle de vie (routing, selection, nettoyage) =====
useMessagesLifecycle({
  route,
  router,
  conversations,
  selectConversation,
  forwardPicker,
  forwardPickerRef,
  showConversationPanel,
  invites,
  clearPendingAttachments,
  resetComposerState,
  resetSearchPanel,
  syncConversationFormFromSelected,
  canManageConversation,
  loadConversationInvites,
  closeTransientMenus,
  cancelForwardSelection,
  closeDeleteDialog,
  messages,
  suppressAutoScroll,
  loadingOlderMessages,
  scrollToBottom,
  selectedConversationId,
  endCall,
  disconnectRealtime,
  loadConversations,
  loadAvailabilityStatus,
  cleanupRemoteTyping,
  handleProfileBroadcast,
  processNotificationPayload,
  ensureMessageVisible,
  reactionPickerFor,
  messageMenuOpen,
})

// ----- Liste des conversations eligibles pour le transfert -----
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


// ===== Navigation et chargement d'une conversation =====
async function selectConversation(convId) {
  const id = String(convId)
  if (!conversations.value.some((conv) => conv.id === id)) return
  const isSame = selectedConversationId.value === id
  selectedConversationId.value = id
  messageInput.value = ''
  resetPickerState()
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

// ----- Utilitaires de scroll pour maintenir la vue a jour -----
function scrollToBottom() {
  messageListRef.value?.scrollToBottom?.()
}

// Redirection vers la creation d'une nouvelle conversation
function goToNewConversation() {

  router.push({ path: '/dashboard/messages/new' }).catch(() => {})

}




// Reinitialise le composer (nouveau message / reponse / transfert)
function resetComposerState() {
  composerState.mode = 'new'
  composerState.targetMessageId = null
  composerState.replyTo = null
  composerState.forwardFrom = null
}

// Genere un identifiant local pour suivre les appels en cours
function generateCallId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `call_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

// Ajoute une entree systeme dans le flux lorsqu'un appel change d'etat
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






// Scroll jusqu'a un message cible (pin, recherche, toast)
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

// Normalise les messages d'erreur en provenance des appels API ou exceptions
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
</script>

<style src="@/assets/styles/messages.css"></style>














































