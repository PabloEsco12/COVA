<template>
  <div class="messages-wrapper">
    <div class="messages-layout">
      <!-- Conversations list -->
      <aside class="conv-list">
        <div class="conv-list-header">
          <div>
            <h2 class="conv-title">Conversations</h2>
            <p class="conv-subtitle">
              {{ totalConversations }} discussion(s) sécurisée(s)
              <span v-if="conversationFilterStats.unread">
                • {{ conversationFilterStats.unread }} non lue(s)
              </span>
            </p>
          </div>
          <button type="button" class="conv-create-btn" @click="openConvModal">
            <i class="bi bi-plus-lg"></i>
          </button>
        </div>
        <div class="conv-tools">
          <div class="input-icon conv-search">
            <i class="bi bi-search"></i>
            <input
              v-model.trim="conversationSearch"
              type="text"
              class="form-control"
              placeholder="Rechercher une conversation"
            />
          </div>
          <div class="conv-meta">
            <span class="conv-meta-chip">
              <i class="bi bi-funnel me-1"></i>{{ activeConversationFilter.label }}
            </span>
            <span class="conv-meta-chip">
              <i class="bi bi-chat-text me-1"></i>{{ filteredConversations.length }} conversation(s)
            </span>
          </div>
        </div>
        <div class="conv-filters">
          <button
            v-for="filter in conversationFilters"
            :key="filter.value"
            type="button"
            class="conv-filter-btn"
            :class="{ active: conversationFilter === filter.value }"
            :aria-pressed="conversationFilter === filter.value"
            @click="setConversationFilter(filter.value)"
          >
            <span class="filter-label">
              <i class="bi" :class="filter.icon"></i>
              <span>{{ filter.label }}</span>
            </span>
            <span class="filter-count">{{ conversationFilterStats[filter.value] ?? 0 }}</span>
          </button>
        </div>
        <div class="conv-scroll">
          <ul class="list-group list-group-flush conv-list-scroll">
            <li
              v-for="conv in filteredConversations"
              :key="conv.id"
              class="list-group-item p-0 border-0 bg-transparent"
            >
              <div
                class="conv-tile"
                :class="{ active: conv.id === selectedConvId, favorite: isFavorite(conv.id) }"
                @click="selectConversation(conv.id)"
              >
                <div class="me-2 avatar-wrap">
                  <img v-if="conv.avatar_url" :src="conv.avatar_url" class="avatar-list" alt="avatar" />
                  <div v-else class="avatar-list-placeholder" :class="{ group: conv.is_group }">
                    {{ initials(conv.displayName || conv.titre) }}
                  </div>
                  <span v-if="conv.is_group" class="group-ind"><i class="bi bi-people-fill"></i></span>
                </div>
                <div class="flex-grow-1 overflow-hidden conv-content">
                  <div class="conv-name-row d-flex align-items-center">
                    <div class="conv-name text-truncate">{{ conv.displayName || conv.titre }}</div>
                    <div class="ms-auto d-flex align-items-center gap-2 conv-meta-right">
                      <button
                        type="button"
                        class="favorite-toggle"
                        :class="{ active: isFavorite(conv.id) }"
                        :aria-pressed="isFavorite(conv.id)"
                        :title="isFavorite(conv.id) ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                        @click.stop="toggleFavorite(conv.id)"
                      >
                        <i class="bi" :class="isFavorite(conv.id) ? 'bi-star-fill' : 'bi-star'"></i>
                      </button>
                      <div class="conv-time">{{ formatTime(conv.last?.ts) }}</div>
                      <span v-if="getUnreadCount(conv)" class="badge-unread">{{ getUnreadCount(conv) }}</span>
                    </div>
                  </div>
                  <div class="conv-preview text-truncate">
                    <span v-if="conv.last && conv.last.sentByMe" class="text-muted">Vous: </span>
                    {{ conv.last ? conv.last.text : 'Aucun message' }}
                  </div>
                  <div class="conv-flags" v-if="conv.is_group || isFavorite(conv.id)">
                    <span v-if="conv.is_group" class="conv-flag">
                      <i class="bi bi-people-fill me-1"></i>Groupe
                    </span>
                    <span v-if="isFavorite(conv.id)" class="conv-flag favorite">
                      <i class="bi bi-star-fill me-1"></i>Favori
                    </span>
                  </div>
                </div>
              </div>
            </li>
            <li v-if="!filteredConversations.length" class="list-group-item text-center text-muted py-4 conv-empty">
              <i class="bi bi-search mb-2 d-block fs-4"></i>
              <span>Aucune conversation trouvée</span>
            </li>
          </ul>
        </div>
      </aside>

      <!-- Chat area -->
      <section class="chat-container">
        <header class="chat-header">
          <div class="chat-header-icon">
            <i class="bi bi-chat-dots"></i>
          </div>
          <div class="chat-topic flex-grow-1">
            <div class="chat-title-row">
              <h3 class="chat-title">{{ currentConvTitle }}</h3>
            </div>
            <p v-if="!typingLabel" class="chat-subtitle">Discussions sécurisées sur COVA</p>
            <p v-else class="chat-subtitle typing">{{ typingLabel }}</p>
            <div class="chat-meta">
              <span class="chat-meta-chip">
                <i class="bi bi-chat-text me-1"></i>{{ displayMessages.length }} message(s)
              </span>
              <span v-if="selectedCallSessions.length" class="chat-meta-chip">
                <i class="bi bi-camera-video me-1"></i>{{ selectedCallSessions.length }} appel(s)
              </span>
              <span v-if="lastMessageAt" class="chat-meta-chip">
                <i class="bi bi-clock-history me-1"></i>Dernier message {{ formatDate(lastMessageAt) }}
              </span>
            </div>
          </div>
          <div class="chat-actions">
            <button class="chat-action-btn" type="button" @click="refresh" title="Rafraîchir">
              <i class="bi bi-arrow-clockwise"></i>
            </button>
            <button
              class="chat-action-btn"
              type="button"
              :disabled="!selectedConvId || !!callActionPending"
              @click="startCall('video')"
              title="Lancer un appel vidéo"
            >
              <span v-if="callActionPending === 'video'" class="spinner-border spinner-border-sm"></span>
              <i v-else class="bi bi-camera-video"></i>
            </button>
            <button
              class="chat-action-btn"
              type="button"
              :disabled="!selectedConvId || !!callActionPending"
              @click="startCall('audio')"
              title="Lancer un appel audio"
            >
              <span v-if="callActionPending === 'audio'" class="spinner-border spinner-border-sm"></span>
              <i v-else class="bi bi-telephone"></i>
            </button>
            <button
              class="chat-action-btn"
              type="button"
              :title="showMessageSearch ? 'Fermer la recherche' : 'Rechercher dans la conversation'"
              @click="toggleMessageSearch"
            >
              <i class="bi bi-search"></i>
            </button>
            <div class="dropdown">
              <button
                class="chat-action-btn dropdown-toggle"
                type="button"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                title="Options"
              >
                <i class="bi bi-three-dots"></i>
              </button>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="#" @click.prevent="promptRename">Renommer</a></li>
                <li><a class="dropdown-item" href="#" @click.prevent="leaveConversation">Quitter la conversation</a></li>
                <li><hr class="dropdown-divider" /></li>
                <li><a class="dropdown-item text-danger" href="#" @click.prevent="deleteConversation">Supprimer</a></li>
              </ul>
            </div>
          </div>
        </header>
      <div v-if="latestCall" class="call-banner" :class="latestCall.call_type">
        <div class="call-banner-info">
          <div class="call-banner-icon">
            <i class="bi" :class="callTypeIcon(latestCall.call_type)"></i>
          </div>
          <div>
            <div class="call-banner-title">{{ callTypeLabel(latestCall.call_type) }}</div>
            <div class="call-banner-meta">
              Lancé par {{ callInitiatorLabel(latestCall) }} · {{ formatDate(latestCall.started_at) }}
            </div>
          </div>
        </div>
        <div class="call-banner-actions">
          <button class="btn btn-primary btn-sm" type="button" @click="joinCall(latestCall)">
            <i class="bi bi-box-arrow-in-right me-1"></i>Rejoindre
          </button>
        </div>
      </div>
      <div v-if="showMessageSearch" class="chat-search">
        <div class="input-group input-group-sm chat-search-bar">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input
            v-model.trim="messageSearch"
            type="text"
            class="form-control"
            placeholder="Rechercher dans la conversation"
            autocomplete="off"
          />
          <button class="btn btn-outline-secondary" type="button" @click="messageSearch = ''" :disabled="!messageSearch">
            <i class="bi bi-x"></i>
          </button>
        </div>
        <div class="row g-2 align-items-center mt-2 chat-search-grid">
          <div class="col-6 col-md-2">
            <select class="form-select form-select-sm" v-model="messageSearchAuthor">
              <option value="all">Tous</option>
              <option value="me">Moi</option>
              <option value="others">Autres</option>
            </select>
          </div>
          <div class="col-6 col-md-2">
            <input type="date" class="form-control form-control-sm" v-model="messageSearchFrom" />
          </div>
          <div class="col-6 col-md-2">
            <input type="date" class="form-control form-control-sm" v-model="messageSearchTo" />
          </div>
          <div class="col-6 col-md-2 text-end">
            <button class="btn btn-sm btn-outline-secondary" type="button" @click="clearMessageFilters">Réinitialiser</button>
          </div>
        </div>
        <div v-if="messageSearch" class="search-result-count small text-muted mt-1">
          {{ displayMessages.length }} résultat(s)
        </div>
      </div>

      <div class="chat-messages" ref="messagesBox" @scroll="onScroll">
        <div v-if="loading" class="chat-state">
          <span class="spinner-border text-primary"></span>
        </div>
        <div v-else-if="messages.length === 0" class="chat-state chat-empty">
          <i class="bi bi-inbox display-4"></i>
          <div>Aucun message pour le moment</div>
        </div>
        <div v-else class="chat-history">
          <div v-if="messageSearch && displayMessages.length === 0" class="chat-state chat-empty">Aucun résultat</div>
          <div v-else class="messages-stack">
            <div v-for="msg in displayMessages" :key="msg.id_msg" class="msg-row" :class="{ sent: msg.sentByMe }">
              <template v-if="!msg.sentByMe && partnerAvatar">
                <img :src="partnerAvatar" class="avatar-xs me-2" alt="avatar" />
              </template>
              <div :class="['chat-bubble', msg.sentByMe ? 'sent' : 'received']">
                <div class="bubble-header">
                  <span class="name">{{ msg.sentByMe ? pseudo : partnerName }}</span>
                  <span class="time">{{ formatDate(msg.ts_msg) }}</span>
                </div>
                <div class="bubble-body">
                  <template v-if="editingId === msg.id_msg">
                    <input v-model="editContent" class="form-control form-control-sm mb-1" />
                    <div class="text-end">
                      <button class="btn btn-sm btn-success me-1" @click="confirmEdit">OK</button>
                      <button class="btn btn-sm btn-secondary" @click="cancelEdit">Annuler</button>
                    </div>
                  </template>
                  <template v-else>
                    {{ msg.contenu_chiffre || (msg.files?.length ? `${msg.files.length} pièce(s) jointe(s)` : '') }}
                  </template>
                </div>

                <div v-if="msg.files && msg.files.length" class="bubble-attachments mt-2">
                  <div
                    v-for="file in msg.files"
                    :key="file.id_file"
                    class="attachment-item"
                    :class="{ preview: isInlineImage(file) }"
                  >
                    <template v-if="isInlineImage(file)">
                      <button
                        type="button"
                        class="attachment-thumb"
                        :aria-label="`Télécharger ${file.filename}`"
                        @click="downloadAttachment(file)"
                      >
                        <img
                          v-if="attachmentPreviews[file.id_file]"
                          :src="attachmentPreviews[file.id_file]"
                          :alt="file.filename"
                        />
                        <span v-else class="spinner-border spinner-border-sm text-primary"></span>
                      </button>
                      <div class="attachment-meta">
                        <div class="attachment-name" v-html="highlightFilename(file.filename)"></div>
                        <small class="text-muted">{{ formatSize(file.taille) }}</small>
                      </div>
                    </template>
                    <template v-else>
                      <i class="bi bi-paperclip me-2"></i>
                      <button class="btn btn-link p-0 attachment-link" type="button" @click="downloadAttachment(file)">
                        <span v-html="highlightFilename(file.filename)"></span>
                      </button>
                      <small class="text-muted ms-2">{{ formatSize(file.taille) }}</small>
                    </template>
                  </div>
                </div>

                <div class="reaction-strip mt-2">
                  <button
                    v-for="reaction in reactionSummary(msg)"
                    :key="reaction.emoji"
                    class="reaction-chip"
                    :class="{ mine: reaction.mine }"
                    type="button"
                    @click="toggleReaction(msg.id_msg, reaction.emoji)"
                  >
                    <span class="emoji">{{ reaction.emoji }}</span>
                    <span class="count">{{ reaction.count }}</span>
                  </button>
                  <div class="reaction-picker" v-if="reactionPickerFor === msg.id_msg">
                    <emoji-picker
                      class="reaction-emoji-picker"
                      skin-tone-emoji="👍"
                      @emoji-click="event => onReactionEmoji(msg.id_msg, event)"
                    ></emoji-picker>
                  </div>
                  <button
                    class="btn btn-light btn-sm add-reaction"
                    type="button"
                    @click="toggleReactionPicker(msg.id_msg)"
                  >
                    <i class="bi bi-emoji-smile"></i>
                  </button>
                </div>

                <div v-if="msg.sentByMe" class="bubble-actions text-end">
                  <button class="btn btn-action me-1" @click="startEdit(msg)" title="Modifier">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-action danger" @click="deleteMessage(msg.id_msg)" title="Supprimer">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <form @submit.prevent="sendMessage" class="chat-input">
        <div class="composer-bar">
          <div class="composer-tools">
            <button
              class="composer-icon"
              type="button"
              :disabled="loading || sendingMessage"
              @click="triggerFilePicker"
              aria-label="Joindre un fichier"
            >
              <i class="bi bi-paperclip"></i>
            </button>
            <input ref="fileInput" type="file" class="d-none" multiple @change="handleFiles" />
            <button
              class="composer-icon"
              type="button"
              :disabled="loading || sendingMessage"
              @click="toggleEmojiPicker"
              aria-label="Insérer un emoji"
            >
              <i class="bi bi-emoji-smile"></i>
            </button>
            <button
              class="composer-icon"
              type="button"
              :disabled="loading || sendingMessage"
              @click="toggleGifPicker"
              aria-label="Ajouter un GIF"
            >
              <i class="bi bi-filetype-gif"></i>
            </button>
          </div>
          <input
            v-model="newMessage"
            type="text"
            class="composer-input"
            placeholder="Écrire un message..."
            :disabled="loading || sendingMessage"
            @keyup.enter="sendMessage"
            @input="handleTyping"
            autocomplete="off"
            ref="messageInput"
          />
          <button class="composer-send" type="submit" :disabled="!canSend || loading || sendingMessage">
            <span v-if="sendingMessage" class="spinner-border spinner-border-sm"></span>
            <i v-else class="bi bi-send"></i>
          </button>
        </div>
        <div v-if="pendingFiles.length" class="pending-files">
          <div v-for="(file, index) in pendingFiles" :key="`${file.name}-${index}`" class="pending-file">
            <div v-if="file.previewUrl" class="pending-thumb">
              <img :src="file.previewUrl" :alt="file.name" />
            </div>
            <div class="pending-details">
              <div class="pending-name text-truncate">{{ file.name }}</div>
              <small class="text-muted">{{ formatSize(file.size) }}</small>
            </div>
            <button type="button" class="btn-close ms-2" aria-label="Retirer" @click="removePendingFile(index)"></button>
          </div>
        </div>
        <div v-if="showEmojiPicker" class="emoji-popover shadow-sm">
          <emoji-picker
            class="composer-emoji-picker"
            skin-tone-emoji="👍"
            @emoji-click="onComposerEmojiSelect"
          ></emoji-picker>
        </div>
        <div v-if="showGifPicker" class="gif-popover shadow-sm">
          <div class="gif-search input-group input-group-sm mb-2">
            <span class="input-group-text"><i class="bi bi-search"></i></span>
            <input
              v-model="gifSearchTerm"
              type="text"
              class="form-control"
              placeholder="Rechercher un GIF"
              autocomplete="off"
            />
            <button
              class="btn btn-outline-secondary"
              type="button"
              :disabled="gifLoading"
              @click="refreshGifResults"
            >
              <i class="bi bi-arrow-clockwise" :class="{ spinning: gifLoading }"></i>
            </button>
          </div>
          <div v-if="gifError" class="gif-error alert alert-warning py-1 px-2 mb-2">{{ gifError }}</div>
          <div v-if="gifLoading" class="gif-loading text-center py-2">
            <span class="spinner-border spinner-border-sm text-primary"></span>
          </div>
          <div v-else>
            <div v-if="gifResults.length" class="gif-grid">
              <button
                v-for="gif in gifResults"
                :key="gif.id"
                type="button"
                class="gif-thumb"
                @click="addGifToPending(gif)"
              >
                <img :src="gif.media_formats?.tinygif?.url || gif.media_formats?.gif?.url" alt="GIF" />
              </button>
            </div>
            <div v-else class="text-muted small text-center py-2">Aucun GIF trouvé</div>
          </div>
        </div>
      </form>
    </section>
  </div>

  <!-- Modal nouvelle conversation (améliorée) -->
  <div v-if="showConvModal" class="modal-backdrop-custom">
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content glass-modal p-0 overflow-hidden">
        <div class="modal-header gradient-header text-white">
          <div>
            <h5 class="modal-title mb-0"><i class="bi bi-people me-2"></i>Nouvelle conversation</h5>
            <small class="d-block opacity-75">Sélectionnez des contacts puis donnez un titre</small>
          </div>
          <button type="button" class="btn-close btn-close-white" aria-label="Fermer" @click="showConvModal = false"></button>
        </div>
        <div class="modal-body p-0">
          <div class="row g-0">
            <div class="col-md-5 border-end p-3">
              <div class="sticky-top bg-white pb-2">
                <div class="input-icon mb-2">
                  <i class="bi bi-search"></i>
                  <input
                    ref="convSearchInput"
                    v-model.trim="convSearch"
                    type="text"
                    class="form-control ps-5"
                    placeholder="Rechercher un contact (nom ou e-mail)"
                  />
                </div>
                <div class="text-muted small ms-1 mb-1">{{ filteredConvContacts.length }} contact(s)</div>
              </div>
              <div class="contact-list mt-1">
                <div
                  v-for="c in filteredConvContacts"
                  :key="c.user_id"
                  class="contact-item d-flex align-items-center justify-content-between"
                  :class="{ selected: isSelected(c.user_id) }"
                  @click="toggleSelect(c.user_id)"
                >
                  <div class="d-flex align-items-center">
                    <span class="check-circle me-2" :class="{ checked: isSelected(c.user_id) }">
                      <i class="bi" :class="isSelected(c.user_id) ? 'bi-check-lg' : 'bi-plus-lg'"></i>
                    </span>
                    <img v-if="c.avatar_url" :src="c.avatar_url" class="avatar-md me-2" alt="avatar" />
                    <div v-else class="avatar-md-placeholder me-2">{{ initials(c.pseudo) }}</div>
                    <div>
                      <div class="fw-semibold">{{ c.pseudo }}</div>
                      <div class="text-muted small">{{ c.email }}</div>
                    </div>
                  </div>
                  <button
                    class="btn btn-sm btn-soft"
                    :class="isSelected(c.user_id) ? 'btn-soft-danger' : 'btn-soft-primary'"
                    @click.stop="toggleSelect(c.user_id)"
                  >
                    {{ isSelected(c.user_id) ? 'Retirer' : 'Ajouter' }}
                  </button>
                </div>
                <div v-if="filteredConvContacts.length === 0" class="text-muted small py-2">Aucun contact</div>
              </div>
            </div>
            <div class="col-md-7 p-4">
              <div class="mb-3">
                <div class="step-label">Étape 1 • Participants</div>
                <div class="selected-chips mt-3">
                  <span v-for="uid in selectedUsers" :key="uid" class="chip">
                    <template v-if="byId(uid)?.avatar_url">
                      <img :src="byId(uid).avatar_url" class="chip-avatar-lg" alt="avatar" />
                    </template>
                    <template v-else>
                      <span class="chip-avatar-lg chip-initials">{{ initials(byId(uid)?.pseudo) }}</span>
                    </template>
                    {{ byId(uid)?.pseudo || uid }}
                    <i class="bi bi-x ms-1" role="button" aria-label="Retirer" @click="removeSelected(uid)"></i>
                  </span>
                  <div v-if="selectedUsers.length === 0" class="text-muted small">
                    Sélectionnez au moins un contact à gauche
                  </div>
                </div>
              </div>

              <div>
                <div class="step-label">Étape 2 • Titre</div>
                <input v-model="convTitle" type="text" class="form-control mt-2" placeholder="Titre de la conversation (obligatoire)" />
                <small v-if="!convTitle && selectedUsers.length" class="text-muted">Suggestion : {{ titleSuggestion }}</small>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer sticky-footer d-flex align-items-center">
          <div class="text-muted small me-auto">{{ selectedUsers.length }} participant(s) sélectionné(s)</div>
          <button class="btn btn-secondary" @click="showConvModal = false">Annuler</button>
          <button class="btn btn-create" @click="createConversation" :disabled="creatingConv || selectedUsers.length === 0 || !convTitle">
            <span v-if="creatingConv" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-chat-dots me-1"></i>
            <span>Créer</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { api, backendBase } from '@/utils/api'
import { io } from 'socket.io-client'
import LogoUrl from '@/assets/logo_COVA.png'
import 'emoji-picker-element'
// backendBase provided by central api util

const conversations = ref([])
const selectedConvId = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const sendingMessage = ref(false)
const messagesBox = ref(null)
const pseudo = localStorage.getItem('pseudo') || 'Moi'
const userId = Number(localStorage.getItem('user_id') || 0)
const editingId = ref(null)
const editContent = ref('')
const showConvModal = ref(false)
const contacts = ref([])
const selectedUsers = ref([])
const convTitle = ref('')
const creatingConv = ref(false)
const currentConvTitle = ref('')
const socket = ref(null)
let lastJoinedConv = null
let markReadTimer = null
let typingSendTimer = null
let gifSearchTimer = null
let gifController = null
const typingLabel = ref('')
const unreadCounts = ref({})
const conversationSearch = ref('')
const conversationFilter = ref('all')
const FAVORITES_STORAGE_KEY = 'favorite_conversations'
const favoriteConversationIds = ref([])
const conversationFilters = [
  { value: 'all', label: 'Tout', icon: 'bi-chat-dots' },
  { value: 'unread', label: 'Non lues', icon: 'bi-envelope-open' },
  { value: 'favorites', label: 'Favoris', icon: 'bi-star' },
  { value: 'groups', label: 'Groupes', icon: 'bi-people' },
]
const loadingPreviewIds = new Set()
function favoriteKey(id) {
  return String(id)
}

function isFavorite(id) {
  const key = favoriteKey(id)
  return favoriteConversationIds.value.includes(key)
}

function applyFavoriteStateToConversations() {
  const set = new Set(favoriteConversationIds.value || [])
  for (const conv of conversations.value || []) {
    conv.isFavorite = set.has(favoriteKey(conv.id))
  }
}

function loadFavorites() {
  try {
    const raw = localStorage.getItem(FAVORITES_STORAGE_KEY)
    if (!raw) {
      favoriteConversationIds.value = []
      return
    }
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      const unique = Array.from(new Set(parsed.map(value => favoriteKey(value))))
      favoriteConversationIds.value = unique
    } else if (parsed && typeof parsed === 'object') {
      const keys = Object.keys(parsed).filter(key => parsed[key]).map(key => favoriteKey(key))
      favoriteConversationIds.value = Array.from(new Set(keys))
    } else {
      favoriteConversationIds.value = []
    }
  } catch {
    favoriteConversationIds.value = []
  }
  applyFavoriteStateToConversations()
}

function saveFavorites() {
  try {
    localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(favoriteConversationIds.value))
  } catch {}
}

function toggleFavorite(id) {
  const key = favoriteKey(id)
  const set = new Set(favoriteConversationIds.value || [])
  if (set.has(key)) set.delete(key)
  else set.add(key)
  favoriteConversationIds.value = Array.from(set)
  applyFavoriteStateToConversations()
  saveFavorites()
}

function removeFavorite(id) {
  const key = favoriteKey(id)
  if (!favoriteConversationIds.value.includes(key)) return
  favoriteConversationIds.value = favoriteConversationIds.value.filter(item => item !== key)
  applyFavoriteStateToConversations()
  saveFavorites()
}

function setConversationFilter(value) {
  conversationFilter.value = value
}

function getUnreadCount(conv) {
  if (!conv) return 0
  const key = favoriteKey(conv.id)
  const stored = Number(unreadCounts.value?.[key] || 0)
  const fromConv = Number(conv.unread_count || 0)
  return Math.max(stored, fromConv)
}

const filteredConversations = computed(() => {
  const q = conversationSearch.value.trim().toLowerCase()
  const filter = conversationFilter.value
  let list = conversations.value || []
  if (filter === 'unread') {
    list = list.filter(conv => getUnreadCount(conv) > 0)
  } else if (filter === 'favorites') {
    list = list.filter(conv => isFavorite(conv.id))
  } else if (filter === 'groups') {
    list = list.filter(conv => conv.is_group)
  }
  if (!q) return list
  return list.filter(conv => {
    const name = (conv.displayName || conv.titre || '').toLowerCase()
    const preview = (conv.last?.text || '').toLowerCase()
    return name.includes(q) || preview.includes(q)
  })
})

const conversationFilterStats = computed(() => {
  const list = conversations.value || []
  const stats = { all: list.length, unread: 0, favorites: 0, groups: 0 }
  for (const conv of list) {
    if (getUnreadCount(conv) > 0) stats.unread += 1
    if (isFavorite(conv.id)) stats.favorites += 1
    if (conv.is_group) stats.groups += 1
  }
  return stats
})

const totalConversations = computed(() => conversations.value.length)
const activeConversationFilter = computed(
  () => conversationFilters.find(filter => filter.value === conversationFilter.value) || conversationFilters[0]
)
const fileInput = ref(null)
const messageInput = ref(null)
const pendingFiles = ref([])
const showEmojiPicker = ref(false)
const showGifPicker = ref(false)
const showMessageSearch = ref(false)
const messageSearch = ref('')
const messageSearchAuthor = ref('all') // all | me | others
const messageSearchFrom = ref('') // yyyy-mm-dd
const messageSearchTo = ref('') // yyyy-mm-dd
const reactionPickerFor = ref(null)
const gifSearchTerm = ref('')
const gifResults = ref([])
const gifLoading = ref(false)
const gifError = ref('')
const attachmentPreviews = ref({})
// Tenor API key can be configured via Vite env (VITE_TENOR_API_KEY). If absent, we fallback to v1 endpoint.
const TENOR_API_KEY = (import.meta?.env?.VITE_TENOR_API_KEY || '').trim()
const TENOR_CLIENT_KEY = 'cova_messaging_ui'
const GIF_PAGE_LIMIT = 24

const canSend = computed(() => newMessage.value.trim().length > 0 || pendingFiles.value.length > 0)

const callSessionsMap = ref({})
const callActionPending = ref('')
const selectedCallSessions = computed(() => {
  const convId = selectedConvId.value
  if (!convId) return []
  return callSessionsMap.value[convId] || []
})
const latestCall = computed(() => {
  const list = selectedCallSessions.value || []
  if (!list.length) return null
  const sorted = list.slice().sort((a, b) => new Date(b.started_at || 0) - new Date(a.started_at || 0))
  return sorted[0] || null
})

const lastMessageAt = computed(() => {
  const list = messages.value || []
  const lastMessageTs = list.length ? list[list.length - 1]?.ts_msg : null
  const callTs = latestCall.value?.started_at || null
  if (lastMessageTs && callTs) {
    return new Date(callTs) > new Date(lastMessageTs) ? callTs : lastMessageTs
  }
  return callTs || lastMessageTs || null
})

const displayMessages = computed(() => {
  let list = messages.value || []
  // Author filter
  if (messageSearchAuthor.value === 'me') list = list.filter(m => m.sender_id === userId)
  else if (messageSearchAuthor.value === 'others') list = list.filter(m => m.sender_id !== userId)
  // Date filters
  if (messageSearchFrom.value) {
    const from = new Date(messageSearchFrom.value)
    from.setHours(0, 0, 0, 0)
    list = list.filter(m => m.ts_msg && new Date(m.ts_msg) >= from)
  }
  if (messageSearchTo.value) {
    const to = new Date(messageSearchTo.value)
    to.setHours(23, 59, 59, 999)
    list = list.filter(m => m.ts_msg && new Date(m.ts_msg) <= to)
  }
  // Text search
  const q = (messageSearch.value || '').toLowerCase().trim()
  if (!q) return list
  const tokens = q.split(/\s+/).filter(Boolean)
  return list.filter(m => {
    const text = (m.contenu_chiffre || '').toLowerCase()
    const inFiles = (m.files || []).some(f => (f.filename || '').toLowerCase().includes(q))
    const tokenMatch = tokens.every(t => text.includes(t))
    return tokenMatch || inFiles
  })
})

function clearMessageFilters() {
  messageSearch.value = ''
  messageSearchAuthor.value = 'all'
  messageSearchFrom.value = ''
  messageSearchTo.value = ''
}

function escapeHtml(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function buildHighlightRegex(q) {
  const tokens = (q || '').toLowerCase().trim().split(/\s+/).filter(Boolean)
  if (!tokens.length) return null
  const escaped = tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  return new RegExp('(' + escaped.join('|') + ')', 'gi')
}

function highlightMatches(text) {
  const q = (messageSearch.value || '').trim()
  if (!q) return escapeHtml(text || '')
  const rx = buildHighlightRegex(q)
  if (!rx) return escapeHtml(text || '')
  return escapeHtml(text || '').replace(rx, '<mark class="hl">$1</mark>')
}

function highlightMessageText(text) {
  return highlightMatches(text)
}

function highlightFilename(name) {
  return highlightMatches(name)
}

function toggleMessageSearch() {
  showMessageSearch.value = !showMessageSearch.value
  if (!showMessageSearch.value) messageSearch.value = ''
}

function loadUnread() {
  try {
    unreadCounts.value = JSON.parse(localStorage.getItem('unread_counts') || '{}') || {}
  } catch {
    unreadCounts.value = {}
  }
}
function saveUnread() {
  try {
    localStorage.setItem('unread_counts', JSON.stringify(unreadCounts.value || {}))
  } catch {}
}

const titleSuggestion = computed(() => {
  const names = selectedUsers.value.map(u => byId(u)?.pseudo || '').filter(Boolean)
  if (names.length <= 2) return names.join(', ')
  return names.slice(0, 2).join(', ') + ' (+' + (names.length - 2) + ')'
})

const contactsMap = computed(() => {
  const map = {}
  for (const c of contacts.value || []) map[c.user_id] = c
  return map
})

const convSearch = ref('')
const convSearchInput = ref(null)
const filteredConvContacts = computed(() => {
  const q = (convSearch.value || '').toLowerCase()
  if (!q) return contacts.value
  return (contacts.value || []).filter(c => (c.pseudo || '').toLowerCase().includes(q) || (c.email || '').toLowerCase().includes(q))
})
function byId(uid) {
  return (contacts.value || []).find(c => c.user_id === uid)
}
function isSelected(uid) {
  return selectedUsers.value.includes(uid)
}
function toggleSelect(uid) {
  const idx = selectedUsers.value.indexOf(uid)
  if (idx >= 0) selectedUsers.value.splice(idx, 1)
  else selectedUsers.value.push(uid)
  if (!convTitle.value) convTitle.value = derivedTitle()
}
function removeSelected(uid) {
  const idx = selectedUsers.value.indexOf(uid)
  if (idx >= 0) selectedUsers.value.splice(idx, 1)
  if (!convTitle.value) convTitle.value = derivedTitle()
}
function initials(name) {
  const n = (name || '').trim()
  if (!n) return 'C'
  const parts = n.split(/\s+/)
  const s = (parts[0]?.[0] || '') + (parts[1]?.[0] || '')
  return (s || n[0]).toUpperCase()
}
function derivedTitle() {
  const names = selectedUsers.value.map(u => byId(u)?.pseudo || '').filter(Boolean)
  if (names.length === 1) return names[0]
  if (names.length === 2) return names.join(', ')
  if (names.length > 2) return `${names[0]}, ${names[1]} (+${names.length - 2})`
  return ''
}
watch(gifSearchTerm, value => {
  if (!showGifPicker.value) return
  if (gifSearchTimer) {
    clearTimeout(gifSearchTimer)
    gifSearchTimer = null
  }
  gifSearchTimer = setTimeout(() => {
    loadGifResults(value)
  }, 350)
})
watch(showEmojiPicker, open => {
  if (open) {
    showGifPicker.value = false
    reactionPickerFor.value = null
  }
})
watch(showGifPicker, open => {
  if (open) {
    showEmojiPicker.value = false
    reactionPickerFor.value = null
    if (!gifResults.value.length) refreshGifResults()
  } else {
    if (gifSearchTimer) {
      clearTimeout(gifSearchTimer)
      gifSearchTimer = null
    }
    if (gifController) {
      gifController.abort()
      gifController = null
    }
    gifSearchTerm.value = ''
    gifError.value = ''
  }
})
watch(showConvModal, async open => {
  if (open) {
    await nextTick()
    try {
      convSearchInput.value?.focus()
    } catch {}
  }
})
watch(selectedUsers, () => {
  if (!convTitle.value) convTitle.value = derivedTitle()
})

function ensureSocket() {
  if (socket.value) return
  try {
    socket.value = io(backendBase, {
      transports: ['websocket'],
      auth: { token: localStorage.getItem('access_token') },
    })
    socket.value.on('typing', payload => {
      if (!payload || payload.conv_id !== selectedConvId.value) return
      typingLabel.value = payload.is_typing ? "Quelqu'un est en train d'écrire..." : ''
    })
    const onMessage = payload => handleIncomingMessage(payload)
    socket.value.on('message_created', onMessage)
    socket.value.on('new_message', onMessage)
    socket.value.on('reaction_updated', payload => {
      if (!payload) return
      applyReactionUpdate(payload.message_id, payload)
    })
    socket.value.on('call_created', handleCallCreated)
  } catch (e) {
    // ignore connection errors
  }
}

function joinRoom(convId) {
  ensureSocket()
  if (!socket.value) return
  if (lastJoinedConv && lastJoinedConv !== convId) {
    socket.value.emit('leave_conversation', { conv_id: lastJoinedConv })
  }
  socket.value.emit('join_conversation', { conv_id: convId })
  lastJoinedConv = convId
}

function handleTyping() {
  ensureSocket()
  if (!socket.value || !selectedConvId.value) return
  socket.value.emit('typing', { conv_id: selectedConvId.value, is_typing: true })
  if (typingSendTimer) clearTimeout(typingSendTimer)
  typingSendTimer = setTimeout(() => {
    socket.value?.emit('typing', { conv_id: selectedConvId.value, is_typing: false })
  }, 1200)
}

function scheduleMarkRead() {
  if (markReadTimer) clearTimeout(markReadTimer)
  markReadTimer = setTimeout(() => {
    markRead()
  }, 300)
}

function markRead() {
  ensureSocket()
  if (!socket.value || !selectedConvId.value) return
  const ids = messages.value.filter(m => !m.sentByMe).map(m => m.id_msg)
  if (ids.length) socket.value.emit('mark_read', { conv_id: selectedConvId.value, message_ids: ids })
}

function onScroll() {
  const el = messagesBox.value
  if (!el) return
  const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 24
  if (nearBottom) scheduleMarkRead()
}

function scrollToBottom() {
  const el = messagesBox.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission().catch(() => {})
  }
}

function showNotification(title, body) {
  if (!('Notification' in window)) return
  if (Notification.permission !== 'granted') return
  const n = new Notification(title || 'Nouveau message', { body: body || '', icon: LogoUrl })
  n.onclick = () => window.focus()
  setTimeout(() => n.close(), 4000)
}

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleString('fr-BE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

async function fetchConversations() {
  try {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/conversations/`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    conversations.value = (res.data || []).map(c => ({ ...c }))
    await enrichConversations()
    applyFavoriteStateToConversations()
    if (!selectedConvId.value && conversations.value.length) {
      selectConversation(conversations.value[0].id)
    }
  } catch (e) {
    conversations.value = []
  }
}

async function enrichConversations() {
  const token = localStorage.getItem('access_token')
  for (const conv of conversations.value) {
    try {
      if (!conv.is_group) {
        const d = await axios.get(`${import.meta.env.VITE_API_URL}/conversations/${conv.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const parts = d.data?.participants || []
        const other = parts.find(p => p.id_user !== userId)
        conv.displayName = other?.pseudo || conv.titre
        conv.other_user_id = other?.id_user
        conv.avatar_url = contactsMap.value[conv.other_user_id]?.avatar_url || null
      } else {
        conv.displayName = conv.titre
        conv.avatar_url = null
      }
    } catch {}
    try {
      const mres = await axios.get(`${import.meta.env.VITE_API_URL}/conversations/${conv.id}/messages/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const arr = mres.data || []
      const last = arr[arr.length - 1]
      if (last) {
        const text = (last.contenu_chiffre || '').trim()
        const fallback = last.files?.length ? `${last.files.length} pièce(s) jointe(s)` : ''
        conv.last = { text: text || fallback || 'Message', ts: last.ts_msg, sentByMe: last.sender_id === userId }
      }
    } catch {}
  }
}

async function fetchMessages() {
  if (!selectedConvId.value) {
    messages.value = []
    return
  }
  loading.value = true
  try {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/messages/`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
  })
    messages.value = (res.data || []).map(m => ({
      ...m,
      sentByMe: m.sender_id === userId,
      files: m.files || [],
      reactions: m.reactions || [],
      reaction_summary: m.reaction_summary || [],
    }))
    await nextTick()
    scrollToBottom()
    scheduleMarkRead()
  } catch (e) {
    messages.value = []
  } finally {
    loading.value = false
  }
}

function refresh() {
  fetchMessages()
}

function normalizeCall(session) {
  if (!session || typeof session !== 'object') return null
  const initiator = session.initiator || null
  return {
    ...session,
    initiator,
    initiator_pseudo: session.initiator_pseudo || initiator?.pseudo || '',
    isMine: session.initiator_id === userId,
  }
}

function setCallSessions(convId, sessions) {
  if (!convId) return
  const safeList = (sessions || []).slice().sort((a, b) => new Date(a.started_at || 0) - new Date(b.started_at || 0))
  callSessionsMap.value = { ...callSessionsMap.value, [convId]: safeList }
}

async function fetchCallSessions(convId = selectedConvId.value) {
  if (!convId) return
  try {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/conversations/${convId}/calls`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const normalized = (res.data || []).map(normalizeCall).filter(Boolean)
    setCallSessions(convId, normalized)
    if (normalized.length) {
      updateConversationPreviewWithCall(normalized[normalized.length - 1])
    }
  } catch (error) {
    setCallSessions(convId, [])
  }
}

function callTypeLabel(type) {
  return type === 'audio' ? 'Appel audio' : 'Appel vidéo'
}

function callTypeIcon(type) {
  return type === 'audio' ? 'bi-telephone-fill' : 'bi-camera-video-fill'
}

function callInitiatorLabel(call) {
  if (!call) return ''
  if (call.isMine) return 'vous'
  return call.initiator_pseudo || call.initiator?.pseudo || 'un membre'
}

function updateConversationPreviewWithCall(call) {
  if (!call) return
  const conv = conversations.value.find(c => c.id === call.conv_id)
  if (!conv) return
  const callTs = call.started_at || null
  const currentTs = conv.last?.ts || null
  if (callTs && currentTs && new Date(currentTs) > new Date(callTs)) return
  conv.last = {
    text: `${callTypeLabel(call.call_type)} démarré`,
    ts: call.started_at,
    sentByMe: call.isMine,
  }
}

function handleCallCreated(payload) {
  const call = normalizeCall(payload)
  if (!call || !call.conv_id) return
  const existing = (callSessionsMap.value[call.conv_id] || []).slice()
  const idx = existing.findIndex(item => item.id === call.id)
  if (idx >= 0) existing[idx] = call
  else existing.push(call)
  existing.sort((a, b) => new Date(a.started_at || 0) - new Date(b.started_at || 0))
  setCallSessions(call.conv_id, existing)
  updateConversationPreviewWithCall(call)
  if (call.conv_id === selectedConvId.value && !call.isMine && document.hidden) {
    showNotification(callTypeLabel(call.call_type), `Lancé par ${callInitiatorLabel(call)}`)
  }
}

async function startCall(callType) {
  if (!selectedConvId.value || callActionPending.value) return
  callActionPending.value = callType
  try {
    const res = await axios.post(
      `${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/calls`,
      { type: callType },
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    const call = normalizeCall(res.data)
    handleCallCreated(call)
    joinCall(call)
  } catch (error) {
    console.error('Unable to start call', error)
    alert("Impossible de démarrer l'appel pour le moment.")
  } finally {
    callActionPending.value = ''
  }
}

function joinCall(call) {
  if (!call || !call.join_url) return
  try {
    window.open(call.join_url, '_blank', 'noopener')
  } catch {}
}

function selectConversation(id) {
  if (selectedConvId.value !== id) {
    selectedConvId.value = id
  }
  const conv = conversations.value.find(c => c.id === id)
  currentConvTitle.value = conv ? conv.displayName || conv.titre : 'Messagerie'
  if (conv) conv.unread_count = 0
  const key = favoriteKey(id)
  if (unreadCounts.value[key]) {
    unreadCounts.value[key] = 0
    saveUnread()
  }
  joinRoom(id)
}

const partnerName = computed(() => {
  const conv = conversations.value.find(c => c.id === selectedConvId.value)
  if (!conv) return 'Utilisateur'
  if (conv.is_group) return 'Membre'
  return conv.displayName || 'Utilisateur'
})
const partnerAvatar = computed(() => {
  const conv = conversations.value.find(c => c.id === selectedConvId.value)
  if (!conv || conv.is_group) return ''
  return conv.avatar_url || ''
})

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  return sameDay
    ? d.toLocaleTimeString('fr-BE', { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString('fr-BE', { day: '2-digit', month: '2-digit' })
}

async function promptRename() {
  if (!selectedConvId.value) return
  const t = prompt('Nouveau titre', currentConvTitle.value || '')
  if (!t || !t.trim()) return
  try {
    await axios.patch(
      `${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/title`,
      { titre: t.trim() },
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    currentConvTitle.value = t.trim()
    await fetchConversations()
  } catch {}
}

async function leaveConversation() {
  if (!selectedConvId.value) return
  const convId = selectedConvId.value
  if (!confirm('Quitter cette conversation ?')) return
  try {
    await axios.post(
      `${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/leave`,
      {},
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    removeFavorite(convId)
    conversations.value = conversations.value.filter(c => c.id !== convId)
    const map = { ...callSessionsMap.value }
    delete map[convId]
    callSessionsMap.value = map
    selectedConvId.value = null
    messages.value = []
    if (conversations.value.length) selectConversation(conversations.value[0].id)
  } catch {}
}

async function deleteConversation() {
  if (!selectedConvId.value) return
  const convId = selectedConvId.value
  if (!confirm('Supprimer définitivement cette conversation ?')) return
  try {
    await axios.delete(`${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    removeFavorite(convId)
    conversations.value = conversations.value.filter(c => c.id !== convId)
    const map = { ...callSessionsMap.value }
    delete map[convId]
    callSessionsMap.value = map
    selectedConvId.value = null
    messages.value = []
    if (conversations.value.length) selectConversation(conversations.value[0].id)
  } catch {}
}

function triggerFilePicker() {
  fileInput.value?.click()
}

function withPreviewForPending(file) {
  if (file && file.type && file.type.startsWith('image/')) {
    try {
      file.previewUrl = URL.createObjectURL(file)
    } catch {}
  }
  return file
}

function revokePendingPreview(file) {
  if (file && file.previewUrl) {
    URL.revokeObjectURL(file.previewUrl)
    delete file.previewUrl
  }
}

function handleFiles(event) {
  const files = Array.from(event.target?.files || []).map(withPreviewForPending)
  if (!files.length) return
  pendingFiles.value = pendingFiles.value.concat(files)
  if (fileInput.value) fileInput.value.value = ''
}

function removePendingFile(index) {
  const removed = pendingFiles.value.splice(index, 1)
  removed.forEach(revokePendingPreview)
}

function resetPendingFiles() {
  pendingFiles.value.forEach(revokePendingPreview)
  pendingFiles.value = []
  if (fileInput.value) fileInput.value.value = ''
}

function toggleEmojiPicker() {
  showEmojiPicker.value = !showEmojiPicker.value
  if (showEmojiPicker.value) {
    showGifPicker.value = false
    reactionPickerFor.value = null
    focusMessageInput()
  }
}

function toggleGifPicker() {
  showGifPicker.value = !showGifPicker.value
  if (showGifPicker.value) {
    showEmojiPicker.value = false
    reactionPickerFor.value = null
    refreshGifResults()
    focusMessageInput()
  }
}

function focusMessageInput() {
  nextTick(() => {
    messageInput.value?.focus()
  })
}

function onComposerEmojiSelect(event) {
  const emoji = extractEmoji(event)
  if (!emoji) return
  newMessage.value += emoji
  showEmojiPicker.value = false
  focusMessageInput()
}

function onReactionEmoji(msgId, event) {
  const emoji = extractEmoji(event)
  if (!emoji) return
  selectReaction(msgId, emoji)
}

function extractEmoji(event) {
  return (
    event?.detail?.unicode ||
    event?.detail?.emoji?.unicode ||
    event?.detail?.native ||
    event?.detail?.char ||
    ''
  )
}

async function refreshGifResults() {
  return loadGifResults(gifSearchTerm.value)
}

async function loadGifResults(query = '') {
  const search = (query || '').trim()
  if (gifController) {
    gifController.abort()
    gifController = null
  }
  const controller = new AbortController()
  gifController = controller
  gifLoading.value = true
  gifError.value = ''
  try {
    if (!TENOR_API_KEY) {
      // No v2 key configured: fallback to legacy v1
      const legacy = await fetchTenorV1(search, controller.signal)
      gifResults.value = legacy
      return
    }
    const endpoint = search ? 'search' : 'featured'
    const params = new URLSearchParams({
      key: TENOR_API_KEY,
      client_key: TENOR_CLIENT_KEY,
      limit: String(GIF_PAGE_LIMIT),
      media_filter: 'minimal',
    })
    if (search) params.set('q', search)
    const response = await fetch(`https://tenor.googleapis.com/v2/${endpoint}?${params.toString()}`, {
      signal: controller.signal,
    })
    if (!response.ok) {
      // Try legacy API when v2 fails (e.g., invalid key)
      const legacy = await fetchTenorV1(search, controller.signal)
      gifResults.value = legacy
      return
    }
    const data = await response.json()
    gifResults.value = data.results || []
  } catch (error) {
    if (error.name === 'AbortError') return
    console.error('GIF search failed', error)
    try {
      const legacy = await fetchTenorV1(search)
      gifResults.value = legacy
      gifError.value = ''
    } catch (e2) {
      gifError.value = "Impossible de charger les GIFs pour le moment."
    }
  } finally {
    if (gifController === controller) {
      gifLoading.value = false
      gifController = null
    }
  }
}

async function fetchTenorV1(search, signal) {
  const endpoint = (search ? 'search' : 'trending')
  const params = new URLSearchParams({
    key: (import.meta?.env?.VITE_TENOR_V1_KEY || 'LIVDSRZULELA'),
    limit: String(GIF_PAGE_LIMIT),
    media_filter: 'minimal',
  })
  if (search) params.set('q', search)
  const res = await fetch(`https://g.tenor.com/v1/${endpoint}?${params.toString()}`, { signal })
  if (!res.ok) throw new Error(`Legacy Tenor HTTP ${res.status}`)
  const data = await res.json()
  return normalizeTenorV1Results(data)
}

function normalizeTenorV1Results(data) {
  const results = data?.results || []
  return results.map(item => {
    const media = Array.isArray(item.media) && item.media.length ? item.media[0] : {}
    const media_formats = {}
    for (const key of ['gif', 'mediumgif', 'nanogif', 'tinygif', 'mp4']) {
      if (media[key]?.url) media_formats[key] = { url: media[key].url }
    }
    return { id: item.id, media_formats }
  })
}

function gifMediaUrl(gif) {
  if (!gif || !gif.media_formats) return ''
  const order = ['gif', 'mediumgif', 'nanogif', 'tinygif', 'loopedmp4']
  for (const key of order) {
    const candidate = gif.media_formats[key]
    if (candidate?.url) return candidate.url
  }
  return ''
}

async function addGifToPending(gif) {
  const url = gifMediaUrl(gif)
  if (!url) {
    gifError.value = 'GIF indisponible.'
    return
  }
  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error('download failed')
    const blob = await response.blob()
    const extension = (blob.type && blob.type.split('/')[1]) || 'gif'
    const filename = `gif-${gif?.id || Date.now()}.${extension}`
    const file = new File([blob], filename, { type: blob.type || 'image/gif' })
    withPreviewForPending(file)
    pendingFiles.value = pendingFiles.value.concat(file)
    showGifPicker.value = false
    gifError.value = ''
    focusMessageInput()
  } catch (error) {
    console.error('Unable to attach GIF', error)
    gifError.value = "Impossible d'ajouter ce GIF."
  }
}

function formatSize(bytes) {
  if (bytes === 0) return '0 o'
  if (!bytes) return ''
  const units = ['o', 'Ko', 'Mo', 'Go']
  let size = bytes
  let idx = 0
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024
    idx += 1
  }
  return `${size % 1 === 0 ? size : size.toFixed(1)} ${units[idx]}`
}

async function sendMessage() {
  if (!selectedConvId.value || sendingMessage.value) return
  if (!canSend.value) return
  const content = newMessage.value
  const attachments = pendingFiles.value.slice()
  const formData = new FormData()
  formData.append('contenu_chiffre', content)
  attachments.forEach(file => formData.append('files', file))
  sendingMessage.value = true
  newMessage.value = ''
  showEmojiPicker.value = false
  showGifPicker.value = false
  try {
    const res = await axios.post(
      `${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/messages/`,
      formData,
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    const created = {
      ...res.data,
      sentByMe: true,
      files: res.data.files || [],
      reactions: res.data.reactions || [],
      reaction_summary: res.data.reaction_summary || [],
    }
    messages.value.push(created)
    resetPendingFiles()
    await nextTick()
    scrollToBottom()
  } catch (e) {
    newMessage.value = content
    pendingFiles.value = attachments
  } finally {
    sendingMessage.value = false
  }
}

function startEdit(msg) {
  editingId.value = msg.id_msg
  editContent.value = msg.contenu_chiffre
}

async function confirmEdit() {
  if (!editingId.value) return
  try {
    await axios.put(
      `${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/messages/${editingId.value}`,
      { contenu_chiffre: editContent.value },
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    editingId.value = null
    editContent.value = ''
    await fetchMessages()
  } catch {}
}

function cancelEdit() {
  editingId.value = null
}

async function deleteMessage(id) {
  if (!confirm('Supprimer ce message ?')) return
  try {
    await axios.delete(
      `${import.meta.env.VITE_API_URL}/conversations/${selectedConvId.value}/messages/${id}`,
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    await fetchMessages()
  } catch {}
}

async function fetchContacts() {
  try {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/contacts?statut=accepted`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    contacts.value = res.data.contacts || []
  } catch {
    contacts.value = []
  }
}

function openConvModal() {
  selectedUsers.value = []
  convTitle.value = ''
  convSearch.value = ''
  fetchContacts()
  showConvModal.value = true
}

async function createConversation() {
  if (!convTitle.value) return
  creatingConv.value = true
  try {
    const res = await axios.post(
      `${import.meta.env.VITE_API_URL}/conversations/`,
      {
        titre: convTitle.value,
        participants: selectedUsers.value,
        is_group: selectedUsers.value.length > 1,
      },
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    showConvModal.value = false
    creatingConv.value = false
    await fetchConversations()
    if (res.data && res.data.id) {
      selectConversation(res.data.id)
      await fetchMessages()
    }
  } catch (e) {
    creatingConv.value = false
  }
}

function reactionSummary(msg) {
  if (msg.reaction_summary && msg.reaction_summary.length) {
    return msg.reaction_summary
  }
  return summariseReactions(msg.reactions || [])
}

function summariseReactions(reactions) {
  const map = new Map()
  for (const reaction of reactions || []) {
    const entry = map.get(reaction.emoji) || { emoji: reaction.emoji, count: 0, mine: false }
    entry.count += 1
    if (reaction.is_mine) entry.mine = true
    map.set(reaction.emoji, entry)
  }
  return Array.from(map.values())
}

function toggleReactionPicker(msgId) {
  reactionPickerFor.value = reactionPickerFor.value === msgId ? null : msgId
  if (reactionPickerFor.value) {
    showEmojiPicker.value = false
    showGifPicker.value = false
  }
}

function selectReaction(msgId, emoji) {
  toggleReaction(msgId, emoji)
  reactionPickerFor.value = null
}

async function toggleReaction(msgId, emoji) {
  try {
    const res = await axios.post(
      `${import.meta.env.VITE_API_URL}/messages/${msgId}/reactions`,
      { emoji },
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    applyReactionUpdate(msgId, res.data)
  } catch {}
}

function applyReactionUpdate(messageId, payload) {
  if (!payload) return
  const target = messages.value.find(m => m.id_msg === messageId)
  if (!target) return
  target.reactions = payload.reactions || []
  target.reaction_summary = payload.reaction_summary || summariseReactions(target.reactions)
}

function attachmentEndpoint(file) {
  const fallback = `/api/messages/files/${file?.id_file}`
  const url = file?.url || fallback
  return url.startsWith('http') ? url : `${backendBase}${url}`
}

function isInlineImage(file) {
  const mime = (file?.mime || '').toLowerCase()
  if (mime.startsWith('image/')) return true
  const name = (file?.filename || '').toLowerCase()
  return /\.(png|jpe?g|gif|webp|bmp)$/i.test(name)
}

async function ensureAttachmentPreview(file) {
  const key = file?.id_file
  if (!key) return
  const cacheKey = String(key)
  if (attachmentPreviews.value[cacheKey] || loadingPreviewIds.has(cacheKey)) return
  if (!isInlineImage(file)) return
  loadingPreviewIds.add(cacheKey)
  try {
    const response = await axios.get(attachmentEndpoint(file), {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const blobUrl = window.URL.createObjectURL(response.data)
    attachmentPreviews.value = { ...attachmentPreviews.value, [cacheKey]: blobUrl }
  } catch (error) {
    console.error('Unable to load preview', error)
  } finally {
    loadingPreviewIds.delete(cacheKey)
  }
}

async function downloadAttachment(file) {
  try {
    const response = await axios.get(attachmentEndpoint(file), {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const blobUrl = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = file.filename || `piece-jointe-${file.id_file}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch {}
}

watch(
  messages,
  list => {
    const active = new Set()
    for (const msg of list || []) {
      for (const file of msg.files || []) {
        if (!file || !file.id_file) continue
        const key = String(file.id_file)
        active.add(key)
        if (isInlineImage(file)) ensureAttachmentPreview(file)
      }
    }
    const cache = { ...attachmentPreviews.value }
    let changed = false
    for (const key of Object.keys(cache)) {
      if (!active.has(key)) {
        window.URL.revokeObjectURL(cache[key])
        delete cache[key]
        changed = true
      }
    }
    if (changed) {
      attachmentPreviews.value = { ...cache }
    }
  },
  { deep: true, immediate: true },
)

function handleIncomingMessage(payload) {
  if (!payload) return
  const normalized = {
    ...payload,
    files: payload.files || [],
    reactions: payload.reactions || [],
    reaction_summary: payload.reaction_summary || [],
    sentByMe: payload.sender_id === userId,
  }
  const already = messages.value.some(m => m.id_msg === normalized.id_msg)
  if (already) {
    applyReactionUpdate(normalized.id_msg, {
      reactions: normalized.reactions,
      reaction_summary: normalized.reaction_summary,
    })
    return
  }
  const convEntry = conversations.value.find(c => c.id === normalized.conv_id)
  if (convEntry) {
    const text = (normalized.contenu_chiffre || '').trim()
    const fallback = normalized.files.length ? `${normalized.files.length} pièce(s) jointe(s)` : ''
    convEntry.last = { text: text || fallback || 'Message', ts: normalized.ts_msg, sentByMe: normalized.sentByMe }
  }
  if (normalized.conv_id === selectedConvId.value) {
    messages.value.push(normalized)
    nextTick().then(() => {
      scrollToBottom()
      if (!normalized.sentByMe) scheduleMarkRead()
    })
    if (!normalized.sentByMe && !document.hasFocus()) {
      const text = (normalized.contenu_chiffre || '').trim()
      const fallback = normalized.files.length ? `${normalized.files.length} pièce(s) jointe(s)` : 'Nouveau message'
      showNotification('Nouveau message', text || fallback)
    }
  } else if (normalized.sender_id !== userId) {
    const key = favoriteKey(normalized.conv_id)
    const nextCount = (unreadCounts.value[key] || 0) + 1
    unreadCounts.value[key] = nextCount
    if (convEntry) convEntry.unread_count = nextCount
    saveUnread()
  } else if (convEntry) {
    convEntry.unread_count = 0
    const key = favoriteKey(normalized.conv_id)
    if (unreadCounts.value[key]) {
      unreadCounts.value[key] = 0
      saveUnread()
    }
  }
}

onMounted(async () => {
  requestNotificationPermission()
  loadUnread()
  loadFavorites()
  await fetchContacts()
  await fetchConversations()
  if (selectedConvId.value) selectConversation(selectedConvId.value)
  await fetchMessages()
  await fetchCallSessions()
  ensureSocket()
  if (selectedConvId.value) joinRoom(selectedConvId.value)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) scheduleMarkRead()
  })
})

watch(selectedConvId, async val => {
  if (val) {
    selectConversation(val)
    await fetchMessages()
    await fetchCallSessions(val)
    resetPendingFiles()
    showEmojiPicker.value = false
    showGifPicker.value = false
    reactionPickerFor.value = null
    typingLabel.value = ''
  }
})

onUnmounted(() => {
  if (gifSearchTimer) {
    clearTimeout(gifSearchTimer)
    gifSearchTimer = null
  }
  if (gifController) {
    gifController.abort()
    gifController = null
  }
  pendingFiles.value.forEach(revokePendingPreview)
  pendingFiles.value = []
  const cache = attachmentPreviews.value || {}
  for (const url of Object.values(cache)) {
    try {
      window.URL.revokeObjectURL(url)
    } catch {}
  }
})
</script>

<style scoped>
/* Create conversation modal styles */
.modal-backdrop-custom .modal-dialog {
  width: clamp(900px, 85vw, 1200px);
  max-width: none;
}
.glass-modal {
  border: 1px solid rgba(13, 110, 253, 0.12);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(16, 24, 40, 0.35);
  background: #fff;
  height: clamp(620px, 80vh, 780px);
  display: flex;
  flex-direction: column;
}
.gradient-header {
  background: linear-gradient(135deg, #2157d3 0%, #1a5ecc 50%, #0d6efd 100%);
}
.input-icon {
  position: relative;
}
.input-icon i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #8aa2d3;
}
.modal-body {
  flex: 1 1 auto;
  overflow: hidden;
}
.contact-list {
  max-height: calc(80vh - 200px);
  overflow-y: auto;
  padding-right: 4px;
}
.contact-item {
  padding: 0.55rem 0.5rem;
  border-bottom: 1px solid #f1f3f7;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}
.contact-item:hover {
  background: #f4f8ff;
}
.contact-item.selected {
  background: #eef4ff;
  border-color: #d9e6ff;
}
.check-circle {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e9eefb;
  color: #668;
  font-size: 0.85rem;
}
.check-circle.checked {
  background: #0d6efd;
  color: #fff;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
}
.contact-item:last-child {
  border-bottom: none;
}
.avatar-md {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}
.avatar-md-placeholder {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e9eefb;
  color: #506;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.selected-chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.7rem;
  border: 1px solid #e8ecf5;
  border-radius: 999px;
  background: #f8faff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.chip-avatar-lg {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}
.chip-initials {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e9eefb;
  color: #506;
  font-weight: 600;
  border-radius: 50%;
  width: 24px;
  height: 24px;
}
.step-label {
  font-weight: 600;
  color: #1f3b76;
  letter-spacing: 0.2px;
}
.btn-soft {
  border: 1px solid transparent;
}
.btn-soft-primary {
  background: #eaf1ff;
  color: #0d6efd;
  border-color: #dbe7ff;
}
.btn-soft-primary:hover {
  background: #e0ebff;
  color: #0a58ca;
}
.btn-soft-danger {
  background: #ffe9ea;
  color: #dc3545;
  border-color: #ffd6d9;
}
.btn-soft-danger:hover {
  background: #ffdfe2;
  color: #bb2d3b;
}
.btn-create {
  background: linear-gradient(135deg, #2157d3, #0d6efd);
  color: #fff;
  border: none;
  box-shadow: 0 10px 24px rgba(13, 110, 253, 0.35);
  padding: 0.6rem 1.1rem;
  font-weight: 600;
}
.btn-create:disabled {
  opacity: 0.65;
  box-shadow: none;
}

/* Chat styles */
.chat-container {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 28px;
  border: 1px solid #d6def2;
  box-shadow: 0 28px 60px rgba(15, 38, 105, 0.15);
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  backdrop-filter: blur(18px);
}
.chat-container::before {
  content: '';
  position: absolute;
  top: -120px;
  left: -80px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(13, 110, 253, 0.18), transparent 70%);
  opacity: 0.4;
  pointer-events: none;
}
.chat-header {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1.5rem 1.75rem 1.25rem;
  border-bottom: 1px solid #e3e8f3;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.55), rgba(239, 243, 255, 0.95));
  z-index: 2;
  box-shadow: 0 12px 30px rgba(15, 38, 105, 0.08);
}
.chat-header-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.18), rgba(13, 110, 253, 0.05));
  color: #2157d3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  box-shadow: inset 0 0 0 1px rgba(13, 110, 253, 0.12);
}
.chat-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.chat-title {
  margin: 0;
  font-size: 1.45rem;
  font-weight: 700;
  color: #152347;
}
.chat-subtitle {
  margin: 0.35rem 0 0;
  color: #6c7898;
  font-size: 0.95rem;
}
.chat-subtitle.typing {
  color: #1f7a55;
  font-weight: 600;
}
.chat-meta {
  margin-top: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.chat-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  border: 1px solid #dbe2f3;
  background: rgba(13, 110, 253, 0.08);
  color: #1f3b76;
  font-weight: 600;
  font-size: 0.8rem;
  letter-spacing: 0.01em;
}
.chat-meta-chip i {
  font-size: 0.9rem;
}
.chat-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.chat-action-btn {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  border: 1px solid #dbe2f3;
  background: #f6f8ff;
  color: #1f3b76;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}
.chat-action-btn:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.18), rgba(13, 110, 253, 0.05));
  border-color: rgba(13, 110, 253, 0.45);
  color: #0d6efd;
  box-shadow: 0 12px 28px rgba(13, 110, 253, 0.18);
}
.chat-action-btn:focus-visible {
  outline: 2px solid rgba(13, 110, 253, 0.3);
  outline-offset: 2px;
}
.chat-action-btn.dropdown-toggle::after {
  display: none;
}
.chat-actions .dropdown-menu {
  border-radius: 16px;
  padding: 0.35rem 0;
  box-shadow: 0 18px 40px rgba(15, 38, 105, 0.12);
}
.call-banner {
  margin: 0 1.75rem 1rem;
  padding: 0.85rem 1.2rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid rgba(13, 110, 253, 0.25);
  background: rgba(13, 110, 253, 0.12);
  color: #123d8c;
  box-shadow: 0 12px 32px rgba(13, 110, 253, 0.12);
}
.call-banner.audio {
  border-color: rgba(25, 135, 84, 0.25);
  background: rgba(25, 135, 84, 0.12);
  color: #0f5132;
}
.call-banner-info {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}
.call-banner-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  font-size: 1.2rem;
}
.call-banner-title {
  font-weight: 700;
  font-size: 1rem;
  margin-bottom: 0.1rem;
}
.call-banner-meta {
  font-size: 0.85rem;
  color: inherit;
  opacity: 0.8;
}
.call-banner-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border-radius: 999px;
  padding-inline: 1rem;
}
.chat-messages {
  position: relative;
  flex: 1;
  padding: 2rem 2.25rem;
  overflow-y: auto;
  background: radial-gradient(circle at top right, rgba(13, 110, 253, 0.08), transparent 65%), #f5f7fb;
}
.chat-messages::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at bottom left, rgba(99, 102, 241, 0.08), transparent 60%);
  opacity: 0.8;
}
.chat-messages > * {
  position: relative;
  z-index: 1;
}
.chat-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 220px;
  color: #6c7898;
  text-align: center;
}
.chat-state.chat-empty i {
  color: #9aa4c3;
}
.chat-history {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.messages-stack {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.chat-bubble {
  max-width: 72%;
  padding: 1rem 1.35rem;
  border-radius: 22px;
  word-break: break-word;
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(211, 222, 243, 0.6);
  box-shadow: 0 18px 38px rgba(15, 38, 105, 0.12);
  backdrop-filter: blur(6px);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.chat-bubble.sent {
  background: linear-gradient(135deg, #2157d3 40%, #0d6efd 100%);
  color: #fff;
  margin-left: auto;
  border-color: transparent;
}
.chat-bubble.received {
  background: rgba(255, 255, 255, 0.92);
  color: #2d3245;
  margin-right: auto;
  border-color: rgba(211, 222, 243, 0.8);
}
.chat-bubble:hover {
  transform: translateY(-1px);
  box-shadow: 0 22px 44px rgba(15, 38, 105, 0.18);
}
.bubble-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  opacity: 0.9;
  margin-bottom: 0.25rem;
}
.bubble-header .name {
  font-weight: 600;
}
.bubble-header .time {
  font-size: 0.78rem;
  color: #8a93ad;
}
.chat-bubble.sent .bubble-header .time {
  color: rgba(255, 255, 255, 0.8);
}
.chat-bubble.sent .bubble-header .name {
  color: #fff;
}
.bubble-body {
  font-size: 1.02em;
  line-height: 1.65;
}
.chat-bubble:after {
  content: '';
  position: absolute;
  bottom: 0;
  width: 14px;
  height: 14px;
  background: inherit;
}
.chat-bubble.received:after {
  left: -6px;
  border-bottom-right-radius: 14px;
  transform: translateY(-2px) rotate(45deg);
  box-shadow: -2px 2px 4px rgba(0, 0, 0, 0.06);
}
.chat-bubble.sent:after {
  right: -6px;
  border-bottom-left-radius: 14px;
  transform: translateY(-2px) rotate(-45deg);
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}
.bubble-actions {
  position: absolute;
  right: 0.4rem;
  bottom: 0.35rem;
  opacity: 0;
  transform: translateY(3px);
  transition: all 0.12s ease;
  pointer-events: none;
}
.chat-bubble:hover .bubble-actions {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}
.btn.btn-action {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  border: none;
  padding: 0.25rem 0.4rem;
  border-radius: 8px;
  backdrop-filter: saturate(140%) blur(2px);
}
.btn.btn-action:hover {
  background: rgba(255, 255, 255, 0.28);
}
.btn.btn-action.danger {
  background: rgba(255, 75, 90, 0.25);
  color: #fff;
}
.btn.btn-action.danger:hover {
  background: rgba(255, 75, 90, 0.35);
}
.chat-input {
  padding: 1.25rem 1.75rem;
  border-top: 1px solid #e3e8f3;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 0 0 28px 28px;
  position: relative;
  box-shadow: 0 -8px 24px rgba(15, 38, 105, 0.08);
}
.composer-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-radius: 18px;
  background: rgba(248, 250, 255, 0.9);
  border: 1px solid #dbe2f3;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.65), 0 12px 30px rgba(15, 38, 105, 0.12);
  padding: 0.6rem 0.75rem;
}
.composer-tools {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.composer-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  border: 1px solid #dbe2f3;
  background: #f6f8ff;
  color: #1f3b76;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.05rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}
.composer-icon:hover:enabled {
  transform: translateY(-2px);
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.18), rgba(13, 110, 253, 0.05));
  border-color: rgba(13, 110, 253, 0.4);
  color: #0d6efd;
  box-shadow: 0 12px 28px rgba(13, 110, 253, 0.18);
}
.composer-icon:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.composer-input {
  flex: 1;
  border: none;
  background: transparent;
  color: #1f2937;
  font-size: 1rem;
  padding: 0.4rem 0.5rem;
}
.composer-input:focus {
  outline: none;
  box-shadow: none;
}
.composer-send {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  border: none;
  background: linear-gradient(135deg, #2157d3, #0d6efd);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  box-shadow: 0 18px 36px rgba(13, 110, 253, 0.28);
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
}
.composer-send:disabled {
  opacity: 0.5;
  box-shadow: none;
  cursor: not-allowed;
}
.composer-send:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 44px rgba(13, 110, 253, 0.32);
}
.pending-files {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.75rem;
}
.pending-file {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem 0.7rem;
  border: 1px solid #dbe2f3;
  border-radius: 14px;
  background: rgba(248, 250, 255, 0.95);
  box-shadow: 0 8px 20px rgba(13, 110, 253, 0.12);
}
.pending-thumb {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  overflow: hidden;
  background: #e5ecff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pending-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.pending-details {
  min-width: 0;
}
.pending-name {
  font-weight: 600;
  max-width: 180px;
}
.emoji-popover,
.gif-popover {
  position: absolute;
  bottom: 90px;
  left: 110px;
  z-index: 30;
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(13, 110, 253, 0.2);
  box-shadow: 0 18px 40px rgba(13, 110, 253, 0.15);
  padding: 0.75rem;
}
.emoji-popover {
  width: 320px;
}
.composer-emoji-picker {
  width: 100%;
  height: 320px;
  border-radius: 12px;
}
.gif-popover {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.gif-search .input-group-text {
  background: #f1f4ff;
  border-color: #dbe2f3;
}
.gif-search .form-control,
.gif-search .btn {
  border-color: #dbe2f3;
}
.chat-search .input-group-text {
  background: rgba(248, 250, 255, 0.95);
  border: none;
  color: #3d4f7c;
}
.chat-search .form-control,
.chat-search .btn,
.chat-search .form-select {
  border: none;
  background: transparent;
  color: #1f3b76;
}
.chat-search .btn {
  color: #1f3b76;
}
.chat-search .btn:hover {
  color: #0d6efd;
}
.chat-search {
  padding: 1.25rem 1.75rem;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid #e3e8f3;
}
.chat-search-bar {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(13, 110, 253, 0.08);
}
.chat-search-bar .form-control {
  padding: 0.6rem 0.9rem;
}
.chat-search-bar .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.chat-search-grid {
  margin-top: 1rem !important;
}
.search-result-count {
  color: #6c7898;
}
mark.hl {
  background: #fff3cd;
  color: inherit;
  padding: 0 2px;
  border-radius: 3px;
}
.chat-search .input-group-text {
  background: #f1f4ff;
  border-color: #dbe2f3;
}
.chat-search .form-control,
.chat-search .btn {
  border-color: #dbe2f3;
}
.gif-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  max-height: 260px;
  overflow-y: auto;
  padding-right: 0.25rem;
}
.gif-thumb {
  border: none;
  padding: 0;
  border-radius: 12px;
  overflow: hidden;
  background: transparent;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(13, 110, 253, 0.14);
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.gif-thumb:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 26px rgba(13, 110, 253, 0.2);
}
.gif-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.gif-loading {
  min-height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.reaction-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.reaction-chip {
  border: 1px solid #dbe2f3;
  border-radius: 999px;
  background: #f0f4ff;
  color: #1f3b76;
  padding: 0.1rem 0.6rem;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.reaction-chip.mine {
  background: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
}
.reaction-chip .emoji {
  font-size: 1rem;
}
.reaction-picker {
  position: relative;
  z-index: 10;
  background: #fff;
  border: 1px solid rgba(13, 110, 253, 0.2);
  border-radius: 14px;
  box-shadow: 0 16px 38px rgba(13, 110, 253, 0.18);
  padding: 0.35rem;
}
.reaction-emoji-picker {
  width: 220px;
  height: 240px;
  border-radius: 12px;
}
.add-reaction {
  border-radius: 999px;
}
.spinning {
  animation: rotate 0.9s linear infinite;
}
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
.bubble-attachments {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.attachment-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.6rem;
  border-radius: 12px;
  background: #f0f4ff;
}
.attachment-item.preview {
  background: #fff;
  border: 1px solid rgba(13, 110, 253, 0.2);
  box-shadow: 0 10px 28px rgba(13, 110, 253, 0.18);
  align-items: stretch;
}
.attachment-thumb {
  border: none;
  background: transparent;
  padding: 0;
  width: 140px;
  height: 140px;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.attachment-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.attachment-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  justify-content: center;
  max-width: 180px;
}
.attachment-name {
  font-weight: 600;
  word-break: break-word;
}
.attachment-item:not(.preview) .attachment-link {
  font-size: 0.95rem;
  font-weight: 600;
}

.conv-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.5rem;
}

.conv-filter-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  border: 1px solid #dbe2f3;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef3ff 100%);
  color: #1f3b76;
  font-weight: 600;
  font-size: 0.78rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
  box-shadow: 0 2px 6px rgba(13, 110, 253, 0.12);
}

.conv-filter-btn .filter-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.conv-filter-btn .filter-label i {
  font-size: 0.85rem;
}

.conv-filter-btn .filter-count {
  background: rgba(13, 110, 253, 0.12);
  color: #0d6efd;
  padding: 0.05rem 0.45rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.72rem;
}

.conv-filter-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(13, 110, 253, 0.22);
}

.conv-filter-btn:focus-visible {
  outline: 2px solid rgba(13, 110, 253, 0.35);
  outline-offset: 2px;
}

.conv-filter-btn.active {
  background: linear-gradient(135deg, #2157d3 0%, #0d6efd 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 10px 24px rgba(13, 110, 253, 0.35);
}

.conv-filter-btn.active .filter-count {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.conv-filter-btn.active .filter-label i,
.conv-filter-btn.active .filter-label span {
  color: inherit;
}

.favorite-toggle {
  border: none;
  background: transparent;
  color: #9aa4b5;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s ease, background 0.15s ease, transform 0.15s ease;
}

.favorite-toggle:hover {
  color: #f3a712;
  background: rgba(243, 167, 18, 0.15);
  transform: translateY(-1px);
}

.favorite-toggle:focus-visible {
  outline: 2px solid rgba(13, 110, 253, 0.4);
  outline-offset: 1px;
}

.favorite-toggle.active {
  color: #f0a400;
}

.conv-tile.active .favorite-toggle {
  color: rgba(255, 255, 255, 0.85);
}

.conv-tile.active .favorite-toggle:hover {
  background: rgba(255, 255, 255, 0.18);
}

.conv-tile.active .favorite-toggle.active {
  color: #ffd976;
}

.conv-tile.favorite:not(.active) {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.12), rgba(255, 193, 7, 0.02));
  border-color: rgba(255, 193, 7, 0.35);
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.18);
}

.messages-wrapper {
  position: relative;
  padding: 1.75rem;
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.07), rgba(255, 255, 255, 0.9));
  border-radius: 32px;
  box-shadow: 0 24px 60px rgba(13, 38, 86, 0.12);
  overflow: hidden;
  margin-bottom: 1.5rem;
}
.messages-wrapper::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top left, rgba(13, 110, 253, 0.12), transparent 55%),
    radial-gradient(circle at bottom right, rgba(99, 102, 241, 0.12), transparent 45%);
  pointer-events: none;
}
.messages-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 1.5rem;
  min-height: clamp(520px, 78vh, 880px);
  width: 100%;
}
.conv-list {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #dbe2f3;
  box-shadow: 0 18px 48px rgba(15, 38, 105, 0.08);
  backdrop-filter: blur(18px);
  overflow: hidden;
}
.conv-list::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(13, 110, 253, 0.15), transparent 65%);
  opacity: 0.6;
  pointer-events: none;
}
.conv-search input {
  border-radius: 14px;
  border: 1px solid #dbe2f3;
  background: rgba(255, 255, 255, 0.85);
  padding-left: 2.6rem;
  height: 42px;
  box-shadow: 0 8px 24px rgba(13, 110, 253, 0.08);
}
.conv-search input:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.18);
  background: #fff;
}
.conv-list-scroll {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}
.conv-list-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}
.conv-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #1f3b76;
}
.conv-subtitle {
  margin: 0.35rem 0 0;
  color: #6c7898;
  font-size: 0.9rem;
}
.conv-create-btn {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: linear-gradient(135deg, #2157d3, #0d6efd);
  color: #fff;
  border: none;
  box-shadow: 0 18px 36px rgba(13, 110, 253, 0.26);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.conv-create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 44px rgba(13, 110, 253, 0.32);
}
.conv-create-btn:focus-visible {
  outline: 2px solid rgba(13, 110, 253, 0.4);
  outline-offset: 2px;
}
.conv-tools {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.conv-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.conv-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  border: 1px solid #dbe2f3;
  background: rgba(13, 110, 253, 0.08);
  color: #1f3b76;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.01em;
}
.conv-meta-chip i {
  font-size: 0.85rem;
}
.conv-scroll {
  flex: 1;
  overflow-y: auto;
  margin: 0 -0.5rem;
  padding: 0 0.5rem 0.5rem;
}
.conv-content {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.conv-name-row {
  gap: 0.5rem;
}
.conv-meta-right {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.conv-preview {
  font-size: 0.92rem;
  color: #6c7898;
}
.conv-flags {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.conv-flag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(13, 110, 253, 0.12);
  color: #1f3b76;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  text-transform: uppercase;
}
.conv-flag.favorite {
  background: rgba(255, 193, 7, 0.2);
  color: #8f6a00;
}
.conv-flag i {
  font-size: 0.75rem;
}
.conv-empty {
  background: transparent;
}
.conv-tile {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border-radius: 20px;
  border: 1px solid transparent;
  background: rgba(248, 250, 255, 0.92);
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
  cursor: pointer;
  box-shadow: 0 12px 28px rgba(15, 38, 105, 0.08);
}
.conv-tile:hover {
  transform: translateY(-3px);
  background: #f0f4ff;
  border-color: rgba(13, 110, 253, 0.18);
  box-shadow: 0 18px 36px rgba(13, 110, 253, 0.16);
}
.conv-tile.active {
  background: linear-gradient(135deg, #2157d3, #0d6efd);
  color: #fff;
  box-shadow: 0 22px 44px rgba(13, 110, 253, 0.35);
}
.avatar-list {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.avatar-list-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e9eefb;
  color: #425;
  font-weight: 700;
}
.avatar-wrap {
  position: relative;
}
.group-ind {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: #0d6efd;
  color: #fff;
  border-radius: 10px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}
.avatar-list-placeholder.group {
  background: #dfe8ff;
}
.conv-name {
  font-weight: 600;
}
.conv-time {
  font-size: 0.8rem;
  color: #7a86a5;
}
.conv-tile.active .conv-time {
  color: #e8f1ff;
}
.conv-preview {
  font-size: 0.92rem;
  color: #6c7898;
}
.conv-tile.active .conv-preview {
  color: rgba(255, 255, 255, 0.85);
  opacity: 1;
}
.conv-tile.active .conv-meta-chip,
.conv-tile.active .conv-flag {
  background: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.85);
  border-color: rgba(255, 255, 255, 0.25);
}
.conv-tile.active .conv-meta-chip i,
.conv-tile.active .conv-flag i {
  color: inherit;
}
.conv-tile.active .conv-time {
  color: rgba(255, 255, 255, 0.75);
}
.badge-unread {
  background: #ff4757;
  color: #fff;
  font-weight: 700;
  font-size: 0.72rem;
  border-radius: 999px;
  padding: 0.15rem 0.45rem;
  box-shadow: 0 2px 6px rgba(255, 71, 87, 0.3);
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  margin: 0;
  animation: bubbleIn 0.16s ease;
}
.msg-row.sent {
  justify-content: flex-end;
}
@media (max-width: 1200px) {
  .messages-layout {
    grid-template-columns: minmax(240px, 280px) minmax(0, 1fr);
  }
}
@media (max-width: 992px) {
  .messages-wrapper {
    padding: 1rem;
  }
  .messages-layout {
    grid-template-columns: 1fr;
    min-height: auto;
    gap: 1rem;
  }
  .conv-list {
    border-radius: 24px;
  }
  .chat-container {
    border-radius: 24px;
  }
}
@media (max-width: 576px) {
  .chat-header {
    flex-wrap: wrap;
    gap: 1rem;
  }
  .chat-actions {
    width: 100%;
    justify-content: flex-start;
  }
  .composer-bar {
    flex-wrap: wrap;
    padding: 0.75rem;
  }
  .composer-input {
    width: 100%;
  }
}
.avatar-xs {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

@keyframes bubbleIn {
  from {
    opacity: 0;
    transform: translateY(4px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(17, 24, 39, 0.45);
  backdrop-filter: blur(6px) saturate(160%);
  -webkit-backdrop-filter: blur(6px) saturate(160%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 2vh 2vw;
}

.sticky-footer {
  position: sticky;
  bottom: 0;
  background: #fff;
  border-top: 1px solid #eef1f6;
  padding: 0.75rem 1rem;
}
</style>
