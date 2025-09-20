<template>
  <div class="messages-layout d-flex">
    <!-- Conversations list -->
    <div class="conv-list p-3">
      <div class="d-flex align-items-center mb-3">
        <strong class="flex-grow-1">Conversations</strong>
        <button class="btn btn-sm btn-primary" @click="openConvModal">
          <i class="bi bi-plus"></i>
        </button>
      </div>
      <ul class="list-group list-group-flush conv-list-scroll">
        <li
          v-for="conv in conversations"
          :key="conv.id"
          class="list-group-item p-0 border-0 bg-transparent"
        >
          <div class="conv-tile" :class="{ active: conv.id === selectedConvId }" @click="selectConversation(conv.id)">
            <div class="me-2 avatar-wrap">
              <img v-if="conv.avatar_url" :src="conv.avatar_url" class="avatar-list" alt="avatar" />
              <div v-else class="avatar-list-placeholder" :class="{ group: conv.is_group }">{{ initials(conv.displayName || conv.titre) }}</div>
              <span v-if="conv.is_group" class="group-ind"><i class="bi bi-people-fill"></i></span>
            </div>
            <div class="flex-grow-1 overflow-hidden">
              <div class="d-flex align-items-center">
                <div class="conv-name text-truncate">{{ conv.displayName || conv.titre }}</div>
                <div class="ms-auto d-flex align-items-center gap-2">
                  <div class="conv-time">{{ formatTime(conv.last?.ts) }}</div>
                  <span v-if="unreadCounts[conv.id]" class="badge-unread">{{ unreadCounts[conv.id] }}</span>
                </div>
              </div>
              <div class="conv-preview text-truncate">
                <span v-if="conv.last && conv.last.sentByMe" class="text-muted">Vous: </span>{{ conv.last ? conv.last.text : 'Aucun message' }}
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Chat area -->
    <div class="chat-container flex-grow-1">
      <div class="chat-header d-flex align-items-center px-3 py-2">
        <i class="bi bi-chat-dots fs-2 text-primary me-3"></i>
        <div class="flex-grow-1">
          <h3 class="mb-0 fw-bold">{{ currentConvTitle }}</h3>
          <small v-if="!typingLabel" class="text-muted">Discussions securisees sur COVA</small>
          <small v-else class="text-success">{{ typingLabel }}</small>
        </div>
        <div class="ms-auto btn-group">
          <button class="btn btn-outline-primary btn-sm" @click="refresh" title="Rafraîchir"><i class="bi bi-arrow-clockwise"></i></button>
          <button class="btn btn-outline-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false" title="Options">
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

      <div class="chat-messages p-3 flex-grow-1" ref="messagesBox" @scroll="onScroll">
        <div v-if="loading" class="text-center py-5"><span class="spinner-border text-primary"></span></div>
        <div v-else-if="messages.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-inbox display-4"></i>
          <div>Aucun message pour le moment</div>
        </div>
        <div v-else>
          <div v-for="msg in messages" :key="msg.id_msg" class="msg-row" :class="{ sent: msg.sentByMe }">
            <template v-if="!msg.sentByMe && partnerAvatar">
              <img :src="partnerAvatar" class="avatar-xs me-2" alt="av" />
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
                <template v-else>{{ msg.contenu_chiffre }}</template>
              </div>
              <div v-if="msg.sentByMe" class="bubble-actions text-end">
                <button class="btn btn-action me-1" @click="startEdit(msg)" title="Modifier"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-action danger" @click="deleteMessage(msg.id_msg)" title="Supprimer"><i class="bi bi-trash"></i></button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <form @submit.prevent="sendMessage" class="chat-input px-3 py-2">
        <div class="input-group">
          <input v-model="newMessage" type="text" class="form-control" placeholder="Ecrire un message..." :disabled="loading" @keyup.enter="sendMessage" @input="handleTyping" autocomplete="off" />
          <button class="btn btn-primary" type="submit" :disabled="!newMessage || loading"><i class="bi bi-send"></i></button>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal nouvelle conversation (amelioree) -->
  <div v-if="showConvModal" class="modal-backdrop-custom">
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content glass-modal p-0 overflow-hidden">
        <div class="modal-header gradient-header text-white">
          <div>
            <h5 class="modal-title mb-0"><i class="bi bi-people me-2"></i>Nouvelle conversation</h5>
            <small class="d-block opacity-75">Selectionnez des contacts puis donnez un titre</small>
          </div>
          <button type="button" class="btn-close btn-close-white" aria-label="Fermer" @click="showConvModal = false"></button>
        </div>
        <div class="modal-body p-0">
          <div class="row g-0">
            <div class="col-md-5 border-end p-3">
              <div class="sticky-top bg-white pb-2">
                <div class="input-icon mb-2">
                  <i class="bi bi-search"></i>
                  <input ref="convSearchInput" v-model.trim="convSearch" type="text" class="form-control ps-5" placeholder="Rechercher un contact (nom ou e-mail)" />
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
                <div class="step-label">Etape 1 • Participants</div>
                <div class="selected-chips mt-3">
                  <span v-for="uid in selectedUsers" :key="uid" class="chip">
                    <template v-if="byId(uid)?.avatar_url"><img :src="byId(uid).avatar_url" class="chip-avatar-lg" alt="av" /></template>
                    <template v-else><span class="chip-avatar-lg chip-initials">{{ initials(byId(uid)?.pseudo) }}</span></template>
                    {{ byId(uid)?.pseudo || uid }}
                    <i class="bi bi-x ms-1" role="button" aria-label="Retirer" @click="removeSelected(uid)"></i>
                  </span>
                  <div v-if="selectedUsers.length === 0" class="text-muted small">Selectionnez au moins un contact a gauche</div>
                </div>
              </div>

              <div>
                <div class="step-label">Etape 2 • Titre</div>
                <input v-model="convTitle" type="text" class="form-control mt-2" placeholder="Titre de la conversation (obligatoire)" />
                <small v-if="!convTitle && selectedUsers.length" class="text-muted">Suggestion: {{ titleSuggestion }}</small>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer sticky-footer d-flex align-items-center">
          <div class="text-muted small me-auto">{{ selectedUsers.length }} participant(s) selectionne(s)</div>
          <button class="btn btn-secondary" @click="showConvModal = false">Annuler</button>
          <button class="btn btn-create" @click="createConversation" :disabled="creatingConv || selectedUsers.length === 0 || !convTitle">
            <span v-if="creatingConv" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-chat-dots me-1"></i>
            <span>Creer</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'
import LogoUrl from '@/assets/logo_COVA.png'

const conversations = ref([])
const selectedConvId = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
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
const typingLabel = ref('')
// Unread counters persisted
const unreadCounts = ref({})
function loadUnread(){
  try{ unreadCounts.value = JSON.parse(localStorage.getItem('unread_counts')||'{}')||{} }catch{ unreadCounts.value = {} }
}
function saveUnread(){
  try{ localStorage.setItem('unread_counts', JSON.stringify(unreadCounts.value||{})) }catch{}
}

// Suggestion simple pour le titre
const titleSuggestion = computed(() => {
  const names = selectedUsers.value.map(u => byId(u)?.pseudo || '').filter(Boolean)
  if (names.length <= 2) return names.join(', ')
  return names.slice(0, 2).join(', ') + ' (+' + (names.length - 2) + ')'
})

// Map rapide id -> contact (pour avatar_url)
const contactsMap = computed(() => {
  const map = {}
  for (const c of (contacts.value || [])) map[c.user_id] = c
  return map
})

// --- Helpers creation conv ---
const convSearch = ref('')
const convSearchInput = ref(null)
const filteredConvContacts = computed(() => {
  const q = (convSearch.value || '').toLowerCase()
  if (!q) return contacts.value
  return (contacts.value || []).filter(c =>
    (c.pseudo || '').toLowerCase().includes(q) || (c.email || '').toLowerCase().includes(q)
  )
})
function byId(uid){ return (contacts.value || []).find(c => c.user_id === uid) }
function isSelected(uid){ return selectedUsers.value.includes(uid) }
function toggleSelect(uid){
  const i = selectedUsers.value.indexOf(uid)
  if (i >= 0) selectedUsers.value.splice(i,1); else selectedUsers.value.push(uid)
  if (!convTitle.value) convTitle.value = derivedTitle()
}
function removeSelected(uid){
  const i = selectedUsers.value.indexOf(uid)
  if (i >= 0) selectedUsers.value.splice(i,1)
  if (!convTitle.value) convTitle.value = derivedTitle()
}
function initials(name){
  const n = (name || '').trim(); if (!n) return 'C'
  const parts = n.split(/\s+/); const s = (parts[0]?.[0]||'')+(parts[1]?.[0]||'')
  return (s || n[0]).toUpperCase()
}
function derivedTitle(){
  const names = selectedUsers.value.map(u => byId(u)?.pseudo || '').filter(Boolean)
  if (names.length === 1) return names[0]
  if (names.length === 2) return names.join(', ')
  if (names.length > 2) return `${names[0]}, ${names[1]} (+${names.length-2})`
  return ''
}
watch(showConvModal, async (open) => {
  if (open) { await nextTick(); try{ convSearchInput.value?.focus(); }catch{} }
})
watch(selectedUsers, () => { if (!convTitle.value) convTitle.value = derivedTitle() })

// Socket init
function ensureSocket2(){
  if (socket.value) return
  try {
    socket.value = io('http://localhost:5000', { transports: ['websocket'] })
    socket.value.on('typing', (payload) => {
      if (!payload || payload.conv_id !== selectedConvId.value) return
      const who = payload.user || "Quelqu'un"
      typingLabel.value = payload.is_typing ? (who + " est en train d'ecrire...") : ''
    })
    socket.value.on('new_message', (payload) => {
      if (!payload) return
      if (payload.conv_id === selectedConvId.value) {
        messages.value.push({ ...payload, sentByMe: payload.sender_id === userId })
        nextTick().then(scrollToBottom)
        if (!document.hasFocus()) {
          showNotification('Nouveau message', payload.contenu_chiffre || '')
        }
      } else if (payload.sender_id !== userId) {
        const cid = String(payload.conv_id)
        unreadCounts.value[cid] = (unreadCounts.value[cid]||0)+1
        saveUnread()
      }
    })
  } catch (e) {
    // ignore
  }
}

// Realtime helpers
function joinRoom(convId) {
  ensureSocket2()
  if (!socket.value) return
  if (lastJoinedConv && lastJoinedConv !== convId) {
    socket.value.emit('leave_conversation', { conv_id: lastJoinedConv })
  }
  socket.value.emit('join_conversation', { conv_id: convId })
  lastJoinedConv = convId
}

function handleTyping() {
  ensureSocket2()
  if (!socket.value || !selectedConvId.value) return
  socket.value.emit('typing', { conv_id: selectedConvId.value, is_typing: true })
  if (typingSendTimer) clearTimeout(typingSendTimer)
  typingSendTimer = setTimeout(() => {
    socket.value?.emit('typing', { conv_id: selectedConvId.value, is_typing: false })
  }, 1200)
}

function scheduleMarkRead() {
  if (markReadTimer) clearTimeout(markReadTimer)
  markReadTimer = setTimeout(() => { markRead() }, 300)
}

function markRead() {
  ensureSocket2()
  if (!socket.value || !selectedConvId.value) return
  const ids = messages.value.filter(m => !m.sentByMe).map(m => m.id_msg)
  if (ids.length) { socket.value.emit('mark_read', { conv_id: selectedConvId.value, message_ids: ids }) }
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

// Format date
function formatDate(ts) {
  const d = new Date(ts)
  return d.toLocaleString('fr-BE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

async function fetchConversations() {
  try {
    const res = await axios.get('http://localhost:5000/api/conversations/', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    conversations.value = (res.data || []).map(c => ({ ...c }))
    await enrichConversations()
    if (!selectedConvId.value && conversations.value.length) {
      selectConversation(conversations.value[0].id)
    }
  } catch (e) {
    conversations.value = []
  }
}

// Enrichit conversations: nom affiché, avatar, dernier message
async function enrichConversations(){
  const token = localStorage.getItem('access_token')
  for (const conv of conversations.value) {
    try {
      if (!conv.is_group) {
        const d = await axios.get(`http://localhost:5000/api/conversations/${conv.id}`, { headers: { Authorization: `Bearer ${token}` } })
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
      const mres = await axios.get(`http://localhost:5000/api/conversations/${conv.id}/messages/`, { headers: { Authorization: `Bearer ${token}` } })
      const arr = mres.data || []
      const last = arr[arr.length - 1]
      if (last) conv.last = { text: last.contenu_chiffre, ts: last.ts_msg, sentByMe: last.sender_id === userId }
    } catch {}
  }
}

async function fetchMessages() {
  if (!selectedConvId.value) { messages.value = []; return }
  loading.value = true
  try {
    const res = await axios.get(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    messages.value = (res.data || []).map(m => ({ ...m, sentByMe: m.sender_id === userId }))
    await nextTick(); scrollToBottom(); scheduleMarkRead()
  } catch (e) {
    messages.value = []
  } finally { loading.value = false }
}

function refresh() { fetchMessages() }

function selectConversation(id) {
  selectedConvId.value = id
  const conv = conversations.value.find(c => c.id === id)
  currentConvTitle.value = conv ? (conv.displayName || conv.titre) : 'Messagerie'
  const key = String(id); if (unreadCounts.value[key]) { unreadCounts.value[key]=0; saveUnread() }
  joinRoom(id)
}

// Infos affichées pour 1‑à‑1
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

function formatTime(ts){
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  return sameDay ? d.toLocaleTimeString('fr-BE', { hour: '2-digit', minute: '2-digit' }) : d.toLocaleDateString('fr-BE', { day: '2-digit', month: '2-digit' })
}

// Actions conv
async function promptRename(){
  if (!selectedConvId.value) return
  const t = prompt('Nouveau titre', currentConvTitle.value || '')
  if (!t || !t.trim()) return
  try {
    await axios.patch(`http://localhost:5000/api/conversations/${selectedConvId.value}/title`, { titre: t.trim() }, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    currentConvTitle.value = t.trim()
    await fetchConversations()
  } catch {}
}
async function leaveConversation(){
  if (!selectedConvId.value) return
  if (!confirm('Quitter cette conversation ?')) return
  try {
    await axios.post(`http://localhost:5000/api/conversations/${selectedConvId.value}/leave`, {}, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    // Retire localement
    conversations.value = conversations.value.filter(c => c.id !== selectedConvId.value)
    selectedConvId.value = null
    messages.value = []
    if (conversations.value.length) selectConversation(conversations.value[0].id)
  } catch {}
}
async function deleteConversation(){
  if (!selectedConvId.value) return
  if (!confirm('Supprimer définitivement cette conversation ?')) return
  try {
    await axios.delete(`http://localhost:5000/api/conversations/${selectedConvId.value}`, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    conversations.value = conversations.value.filter(c => c.id !== selectedConvId.value)
    selectedConvId.value = null
    messages.value = []
    if (conversations.value.length) selectConversation(conversations.value[0].id)
  } catch {}
}

// Send message (REST); WS broadcast will update other clients
async function sendMessage() {
  if (!newMessage.value.trim() || !selectedConvId.value) return
  const content = newMessage.value
  newMessage.value = ''
  try {
    await axios.post(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/`, { contenu_chiffre: content }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    messages.value.push({ id_msg: Date.now(), contenu_chiffre: content, sender_id: userId, conv_id: selectedConvId.value, ts_msg: new Date().toISOString(), sentByMe: true })
    await nextTick(); scrollToBottom()
  } catch (e) {}
}

function startEdit(msg) { editingId.value = msg.id_msg; editContent.value = msg.contenu_chiffre }
async function confirmEdit() {
  if (!editingId.value) return
  try {
    await axios.put(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/${editingId.value}`, { contenu_chiffre: editContent.value }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    editingId.value = null; editContent.value = ''; await fetchMessages()
  } catch {}
}
function cancelEdit() { editingId.value = null }
async function deleteMessage(id) {
  if (!confirm('Supprimer ce message ?')) return
  try {
    await axios.delete(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    await fetchMessages()
  } catch {}
}

async function fetchContacts() {
  try {
    const res = await axios.get('http://localhost:5000/api/contacts?statut=accepted', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    contacts.value = res.data.contacts || []
  } catch { contacts.value = [] }
}
function openConvModal() { selectedUsers.value = []; convTitle.value = ''; fetchContacts(); showConvModal.value = true }
async function createConversation() {
  if (!convTitle.value) return
  // Empêche les doublons 1‑à‑1: si une conv privée existe déjà avec cet utilisateur, ouvrir celle‑ci
  if (selectedUsers.value.length === 1) {
    const target = selectedUsers.value[0]
    const existing = conversations.value.find(c => !c.is_group && (c.other_user_id === target))
    if (existing) { showConvModal.value = false; selectConversation(existing.id); await fetchMessages(); return }
  }
  creatingConv.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/conversations/', {
      titre: convTitle.value, participants: selectedUsers.value, is_group: selectedUsers.value.length > 1
    }, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    showConvModal.value = false; creatingConv.value = false
    await fetchConversations()
    if (res.data && res.data.id) { selectConversation(res.data.id); await fetchMessages() }
  } catch (e) { creatingConv.value = false }
}

onMounted(async () => {
  requestNotificationPermission()
  loadUnread()
  await fetchContacts()
  await fetchConversations()
  if (selectedConvId.value) selectConversation(selectedConvId.value)
  await fetchMessages()
  ensureSocket2()
  if (selectedConvId.value) joinRoom(selectedConvId.value)
  document.addEventListener('visibilitychange', () => { if (!document.hidden) scheduleMarkRead() })
})

watch(selectedConvId, async (val) => {
  if (val) { selectConversation(val); await fetchMessages() }
})
</script>

<style scoped>
/* Create conversation modal styles */
.modal-backdrop-custom .modal-dialog{ width: clamp(900px, 85vw, 1200px); max-width: none; }
.glass-modal { border: 1px solid rgba(13, 110, 253, 0.12); border-radius: 20px; box-shadow: 0 20px 60px rgba(16, 24, 40, 0.35); background: #fff; height: clamp(620px, 80vh, 780px); display:flex; flex-direction:column; }
.gradient-header { background: linear-gradient(135deg, #2157d3 0%, #1a5ecc 50%, #0d6efd 100%); }
.input-icon { position: relative; }
.input-icon i { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8aa2d3; }
.modal-body{ flex: 1 1 auto; overflow:hidden; }
.contact-list{ max-height: calc(80vh - 200px); overflow-y:auto; padding-right: 4px; }
.contact-item{ padding:.55rem .5rem; border-bottom:1px solid #f1f3f7; transition: background-color .15s ease, border-color .15s ease; }
.contact-item:hover{ background:#f4f8ff; }
.contact-item.selected{ background:#eef4ff; border-color:#d9e6ff; }
.check-circle{ width: 20px; height: 20px; border-radius: 999px; display:inline-flex; align-items:center; justify-content:center; background:#e9eefb; color:#668; font-size:.85rem; }
.check-circle.checked{ background:#0d6efd; color:#fff; box-shadow: 0 0 0 3px rgba(13,110,253,.15); }
.contact-item:last-child{ border-bottom:none; }
.avatar-md { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
.avatar-md-placeholder { width: 44px; height: 44px; border-radius: 50%; display:flex; align-items:center; justify-content:center; background:#e9eefb; color:#506; font-weight:600; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.selected-chips{ display:flex; gap:.5rem; flex-wrap:wrap; }
.chip{ display:inline-flex; align-items:center; gap:.35rem; padding:.35rem .7rem; border:1px solid #e8ecf5; border-radius:999px; background:#f8faff; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
.chip-avatar-lg{ width:24px; height:24px; border-radius:50%; object-fit:cover; }
.chip-initials{ display:inline-flex; align-items:center; justify-content:center; background:#e9eefb; color:#506; font-weight:600; border-radius:50%; width:24px; height:24px; }
.step-label{ font-weight: 600; color:#1f3b76; letter-spacing:.2px; }
.btn-soft { border: 1px solid transparent; }
.btn-soft-primary{ background:#eaf1ff; color:#0d6efd; border-color:#dbe7ff; }
.btn-soft-primary:hover{ background:#e0ebff; color:#0a58ca; }
.btn-soft-danger{ background:#ffe9ea; color:#dc3545; border-color:#ffd6d9; }
.btn-soft-danger:hover{ background:#ffdfe2; color:#bb2d3b; }
.btn-create{ background: linear-gradient(135deg, #2157d3, #0d6efd); color:#fff; border:none; box-shadow: 0 10px 24px rgba(13,110,253,.35); padding:.6rem 1.1rem; font-weight:600; }
.btn-create:disabled{ opacity:.65; box-shadow:none; }

/* Chat styles */
.chat-container { background: #f7f9fb; border-radius: 18px; box-shadow: 0 2px 16px #163b7c19; height: 75vh; display: flex; flex-direction: column; min-width: 0; }
.chat-header { border-bottom: 1px solid #e6eaf1; background: #fff; border-radius: 18px 18px 0 0; }
.chat-messages { flex-grow: 1; overflow-y: auto; background: #f7f9fb; }
.chat-bubble { margin-bottom: 14px; max-width: 78%; padding: 0.8rem 1.2rem; border-radius: 18px; word-break: break-word; position: relative; background: #fff; box-shadow: 0 2px 8px #163b7c11; }
.chat-bubble.sent { background: linear-gradient(120deg, #2157d3 55%, #0d6efd 100%); color: #fff; margin-left: auto; text-align: left; }
.chat-bubble.received { background: #fff; color: #2d3245; margin-right: auto; text-align: left; }
.bubble-header { display:flex; align-items:center; gap:.5rem; font-size: .85rem; opacity:.9; margin-bottom: .25rem; }
.bubble-header .name { font-weight:600; }
.bubble-header .time { font-size: .78rem; color: #8a93ad; }
.chat-bubble.sent .bubble-header .time { color: rgba(255,255,255,.8); }
.chat-bubble.sent .bubble-header .name { color: #fff; }
.bubble-body { font-size: 1.02em; line-height: 1.6; }
.chat-bubble:after { content:""; position:absolute; bottom:0; width:14px; height:14px; background: inherit; }
.chat-bubble.received:after { left:-6px; border-bottom-right-radius: 14px; transform: translateY(-2px) rotate(45deg); box-shadow: -2px 2px 4px rgba(0,0,0,.06); }
.chat-bubble.sent:after { right:-6px; border-bottom-left-radius: 14px; transform: translateY(-2px) rotate(-45deg); box-shadow: 2px 2px 4px rgba(0,0,0,.10); }
.bubble-actions{ position:absolute; right:.4rem; bottom:.35rem; opacity:0; transform: translateY(3px); transition: all .12s ease; pointer-events:none; }
.chat-bubble:hover .bubble-actions{ opacity:1; transform: translateY(0); pointer-events:auto; }
.btn.btn-action{ background: rgba(255,255,255,.18); color:#fff; border:none; padding:.25rem .4rem; border-radius:8px; backdrop-filter: saturate(140%) blur(2px); }
.btn.btn-action:hover{ background: rgba(255,255,255,.28); }
.btn.btn-action.danger{ background: rgba(255,75,90,.25); color:#fff; }
.btn.btn-action.danger:hover{ background: rgba(255,75,90,.35); }
.chat-input { border-top: 1px solid #e6eaf1; background: #fff; border-radius: 0 0 18px 18px; }
.bubble-actions button { margin-left: 4px; }
.messages-layout { height: 75vh; background: #fff; border-radius: 18px; box-shadow: 0 2px 16px #163b7c19; }
.conv-list { width: 240px; border-right: 1px solid #e6eaf1; overflow-y: auto; background: #f7f9fb; border-radius: 18px 0 0 18px; }
.conv-item { cursor: pointer; }
.conv-item.active { background: #0d6efd; color: #fff; }
.modal-backdrop-custom { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(17, 24, 39, 0.45); backdrop-filter: blur(6px) saturate(160%); -webkit-backdrop-filter: blur(6px) saturate(160%); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 2vh 2vw; }

/* Footer stays visible */
.sticky-footer{ position: sticky; bottom: 0; background:#fff; border-top: 1px solid #eef1f6; padding: .75rem 1rem; }

/* Conversations list, pro style */
.conv-list-scroll { overflow-y: auto; padding-right: 4px; }
.conv-tile { display: flex; align-items: center; gap:.5rem; padding:.55rem .5rem; border-radius: 12px; border:1px solid transparent; transition: background .15s ease, border-color .15s ease, box-shadow .15s ease; cursor: pointer; }
.conv-tile:hover { background:#f3f6ff; border-color:#e4ebff; }
.conv-tile.active { background:#0d6efd; color:#fff; box-shadow: 0 3px 10px rgba(13,110,253,.25); }
.avatar-list { width: 40px; height: 40px; border-radius:50%; object-fit:cover; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.avatar-list-placeholder { width: 40px; height: 40px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:#e9eefb; color:#425; font-weight:700; }
.avatar-wrap{ position: relative; }
.group-ind{ position: absolute; bottom:-4px; right:-4px; background:#0d6efd; color:#fff; border-radius:10px; width:18px; height:18px; display:flex; align-items:center; justify-content:center; font-size:.75rem; box-shadow: 0 1px 4px rgba(0,0,0,.15); }
.avatar-list-placeholder.group{ background:#dfe8ff; }
.conv-name { font-weight: 600; }
.conv-time { font-size: .8rem; color:#7a86a5; }
.conv-tile.active .conv-time { color:#e8f1ff; }
.conv-preview { font-size: .92rem; color:#6c7898; }
.conv-tile.active .conv-preview { color:#eaf2ff; opacity:.9; }
.badge-unread{ background:#ff4757; color:#fff; font-weight:700; font-size:.72rem; border-radius:999px; padding:.15rem .45rem; box-shadow: 0 2px 6px rgba(255,71,87,.3); }

/* Row around bubbles */
.msg-row { display:flex; align-items:flex-end; gap:.5rem; margin-bottom:10px; animation: bubbleIn .16s ease; }
.msg-row.sent { justify-content: flex-end; }
.avatar-xs { width: 28px; height:28px; border-radius:50%; object-fit:cover; box-shadow: 0 1px 3px rgba(0,0,0,.08); }

@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(4px) scale(.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Conversations list, pro style */
.conv-list-scroll { overflow-y: auto; padding-right: 4px; }
.conv-tile { display: flex; align-items: center; gap:.5rem; padding:.55rem .5rem; border-radius: 12px; border:1px solid transparent; transition: background .15s ease, border-color .15s ease, box-shadow .15s ease; cursor: pointer; }
.conv-tile:hover { background:#f3f6ff; border-color:#e4ebff; }
.conv-tile.active { background:#0d6efd; color:#fff; box-shadow: 0 3px 10px rgba(13,110,253,.25); }
.avatar-list { width: 40px; height: 40px; border-radius:50%; object-fit:cover; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.avatar-list-placeholder { width: 40px; height: 40px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:#e9eefb; color:#425; font-weight:700; }
.conv-name { font-weight: 600; }
.conv-time { font-size: .8rem; color:#7a86a5; }
.conv-tile.active .conv-time { color:#e8f1ff; }
.conv-preview { font-size: .92rem; color:#6c7898; }
.conv-tile.active .conv-preview { color:#eaf2ff; opacity:.9; }

/* Row around bubbles */
.msg-row { display:flex; align-items:flex-end; gap:.5rem; margin-bottom:10px; }
.msg-row.sent { justify-content: flex-end; }
.avatar-xs { width: 28px; height:28px; border-radius:50%; object-fit:cover; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
</style>
