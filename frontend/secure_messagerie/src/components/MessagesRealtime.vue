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
      <ul class="list-group list-group-flush">
        <li
          v-for="conv in conversations"
          :key="conv.id"
          class="list-group-item conv-item"
          :class="{ active: conv.id === selectedConvId }"
          @click="selectConversation(conv.id)"
        >
          {{ conv.titre }}
        </li>
      </ul>
    </div>

    <!-- Chat area -->
    <div class="chat-container flex-grow-1">
      <div class="chat-header d-flex align-items-center px-3 py-2">
        <i class="bi bi-chat-dots fs-2 text-primary me-3"></i>
        <div class="flex-grow-1">
          <h3 class="mb-0 fw-bold">{{ currentConvTitle }}</h3>
          <small v-if="!typingLabel" class="text-muted">Discussions s√©curis√©es sur COVA</small>
          <small v-else class="text-success">{{ typingLabel }}</small>
        </div>
        <div class="ms-auto">
          <button class="btn btn-outline-primary btn-sm" @click="refresh"><i class="bi bi-arrow-clockwise"></i></button>
        </div>
      </div>

      <div class="chat-messages p-3 flex-grow-1" ref="messagesBox" @scroll="onScroll">
        <div v-if="loading" class="text-center py-5"><span class="spinner-border text-primary"></span></div>
        <div v-else-if="messages.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-inbox display-4"></i>
          <div>Aucun message pour le moment</div>
        </div>
        <div v-else>
          <div v-for="msg in messages" :key="msg.id_msg" :class="['chat-bubble', msg.sentByMe ? 'sent' : 'received']">
            <div class="bubble-header">
              <span class="fw-bold text-primary">{{ msg.sentByMe ? pseudo : 'Utilisateur' }}</span>
              <span class="text-muted small ms-2">{{ formatDate(msg.ts_msg) }}</span>
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
            <div v-if="msg.sentByMe" class="bubble-actions text-end mt-1">
              <button class="btn btn-outline-secondary btn-sm me-1" @click="startEdit(msg)"><i class="bi bi-pencil"></i></button>
              <button class="btn btn-outline-danger btn-sm" @click="deleteMessage(msg.id_msg)"><i class="bi bi-trash"></i></button>
            </div>
          </div>
        </div>
      </div>

      <form @submit.prevent="sendMessage" class="chat-input px-3 py-2">
        <div class="input-group">
          <input v-model="newMessage" type="text" class="form-control" placeholder="√âcrire un message..." :disabled="loading" @keyup.enter="sendMessage" @input="handleTyping" autocomplete="off" />
          <button class="btn btn-primary" type="submit" :disabled="!newMessage || loading"><i class="bi bi-send"></i></button>
        </div>
      </form>
    </div>
  </div>

    <!-- Modal nouvelle conversation (amÈliorÈe) -->
  <div v-if="showConvModal" class="modal-backdrop-custom">
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content p-0 overflow-hidden">
        <div class="modal-header bg-light">
          <h5 class="modal-title"><i class="bi bi-people me-2"></i>Nouvelle conversation</h5>
          <button type="button" class="btn-close" @click="showConvModal = false"></button>
        </div>
        <div class="modal-body p-0">
          <div class="row g-0">
            <div class="col-md-5 border-end p-3">
              <div class="mb-2">
                <input ref="convSearchInput" v-model.trim="convSearch" type="text" class="form-control" placeholder="Rechercher un contact (nom ou e-mail)" />
              </div>
              <div class="contact-list">
                <div v-for="c in filteredConvContacts" :key="c.user_id" class="contact-item d-flex align-items-center justify-content-between">
                  <div class="d-flex align-items-center">
                    <img v-if="c.avatar_url" :src="c.avatar_url" class="avatar-sm me-2" alt="avatar" />
                    <div v-else class="avatar-sm-placeholder me-2">{{ initials(c.pseudo) }}</div>
                    <div>
                      <div class="fw-semibold">{{ c.pseudo }}</div>
                      <div class="text-muted small">{{ c.email }}</div>
                    </div>
                  </div>
                  <button class="btn btn-sm" :class="isSelected(c.user_id) ? 'btn-outline-danger' : 'btn-outline-primary'" @click="toggleSelect(c.user_id)">
                    <i :class="isSelected(c.user_id) ? 'bi bi-dash' : 'bi bi-plus'" class="me-1"></i>
                    {{ isSelected(c.user_id) ? 'Retirer' : 'Ajouter' }}
                  </button>
                </div>
                <div v-if="filteredConvContacts.length === 0" class="text-muted small py-2">Aucun contact</div>
              </div>
            </div>
            <div class="col-md-7 p-3">
              <label class="form-label">Titre de la conversation</label>
              <input v-model="convTitle" type="text" class="form-control mb-3" placeholder="Titre (obligatoire)" />
              <label class="form-label">Participants</label>
              <div class="selected-chips mb-3">
                <span v-for="uid in selectedUsers" :key="uid" class="chip">
                  <template v-if="byId(uid)?.avatar_url"><img :src="byId(uid).avatar_url" class="chip-avatar" alt="av" /></template>
                  <template v-else><span class="chip-avatar chip-initials">{{ initials(byId(uid)?.pseudo) }}</span></template>
                  {{ byId(uid)?.pseudo || uid }}
                  <i class="bi bi-x ms-1" role="button" @click="removeSelected(uid)"></i>
                </span>
                <div v-if="selectedUsers.length === 0" class="text-muted small">SÈlectionne au moins un contact ‡ gauche</div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showConvModal = false">Annuler</button>
          <button class="btn btn-primary" @click="createConversation" :disabled="creatingConv || selectedUsers.length === 0 || !convTitle">
            <span v-if="creatingConv" class="spinner-border spinner-border-sm"></span>
            <span v-else>CrÈer</span>
          </button>
        </div>
      </div>
    </div>
  </div></template>

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
// --- Conversation creation helpers ---
const convSearch = ref('');
const convSearchInput = ref(null);
const filteredConvContacts = computed(() => {
  const q = (convSearch.value || '').toLowerCase();
  if (!q) return contacts.value;
  return (contacts.value || []).filter(c =>
    (c.pseudo || '').toLowerCase().includes(q) || (c.email || '').toLowerCase().includes(q)
  );
});
function byId(uid){ return (contacts.value || []).find(c => c.user_id === uid); }
function isSelected(uid){ return selectedUsers.value.includes(uid); }
function toggleSelect(uid){
  const i = selectedUsers.value.indexOf(uid);
  if (i >= 0) selectedUsers.value.splice(i,1); else selectedUsers.value.push(uid);
  if (!convTitle.value) convTitle.value = derivedTitle();
}
function removeSelected(uid){
  const i = selectedUsers.value.indexOf(uid);
  if (i >= 0) selectedUsers.value.splice(i,1);
  if (!convTitle.value) convTitle.value = derivedTitle();
}
function initials(name){
  const n = (name || '').trim(); if (!n) return 'C';
  const parts = n.split(/\s+/); const s = (parts[0]?.[0]||'')+(parts[1]?.[0]||'');
  return (s || n[0]).toUpperCase();
}
function derivedTitle(){
  const names = selectedUsers.value.map(u => byId(u)?.pseudo || '').filter(Boolean);
  if (names.length === 1) return names[0];
  if (names.length === 2) return names.join(', ');
  if (names.length > 2) return `${names[0]}, ${names[1]} (+${names.length-2})`;
  return '';
}watch(showConvModal, async (open) => {
  if (open) { await nextTick(); try{ convSearchInput.value?.focus(); }catch{} }
});
watch(selectedUsers, () => { if (!convTitle.value) convTitle.value = derivedTitle(); });function joinRoom(convId) {
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
  if (ids.length) {
    socket.value.emit('mark_read', { conv_id: selectedConvId.value, message_ids: ids })
  }
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
    conversations.value = res.data || []
    if (!selectedConvId.value && conversations.value.length) {
      selectConversation(conversations.value[0].id)
    }
  } catch (e) {
    conversations.value = []
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
    await nextTick()
    scrollToBottom()
    scheduleMarkRead()
  } catch (e) {
    messages.value = []
  } finally {
    loading.value = false
  }
}

function refresh() { fetchMessages() }

function selectConversation(id) {
  selectedConvId.value = id
  const conv = conversations.value.find(c => c.id === id)
  currentConvTitle.value = conv ? conv.titre : 'Messagerie'
  joinRoom(id)
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
    // Optimistic: append locally; server will also echo via WS
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
  await fetchConversations()
  if (selectedConvId.value) selectConversation(selectedConvId.value)
  await fetchMessages()
  ensureSocket()
  if (selectedConvId.value) joinRoom(selectedConvId.value)
  document.addEventListener('visibilitychange', () => { if (!document.hidden) scheduleMarkRead() })
})

watch(selectedConvId, async (val, oldVal) => {
  if (val) {
    selectConversation(val)
    await fetchMessages()
  }
})
</script>

<style scoped>
/* Create conversation modal styles */
.contact-list{ max-height: 340px; overflow-y:auto; }
.contact-item{ padding:.4rem .25rem; border-bottom:1px solid #f1f3f7; }
.contact-item:last-child{ border-bottom:none; }
.avatar-sm { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
.avatar-sm-placeholder { width: 36px; height: 36px; border-radius: 50%; display:flex; align-items:center; justify-content:center; background:#e9eefb; color:#506; font-weight:600; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.selected-chips{ display:flex; gap:.5rem; flex-wrap:wrap; }
.chip{ display:inline-flex; align-items:center; gap:.25rem; padding:.25rem .5rem; border:1px solid #e8ecf5; border-radius:999px; background:#f8faff; }
.chip-avatar{ width:20px; height:20px; border-radius:50%; object-fit:cover; }
.chip-initials{ display:inline-flex; align-items:center; justify-content:center; background:#e9eefb; color:#506; font-weight:600; }
.chat-container { background: #f7f9fb; border-radius: 18px; box-shadow: 0 2px 16px #163b7c19; height: 75vh; display: flex; flex-direction: column; min-width: 0; }
.chat-header { border-bottom: 1px solid #e6eaf1; background: #fff; border-radius: 18px 18px 0 0; }
.chat-messages { flex-grow: 1; overflow-y: auto; background: #f7f9fb; }
.chat-bubble { margin-bottom: 14px; max-width: 78%; padding: 0.8rem 1.2rem; border-radius: 18px; word-break: break-word; position: relative; background: #fff; box-shadow: 0 2px 8px #163b7c11; }
.chat-bubble.sent { background: linear-gradient(120deg, #2157d3 60%, #1959c2 100%); color: #fff; margin-left: auto; text-align: right; }
.chat-bubble.received { background: #fff; color: #2d3245; margin-right: auto; text-align: left; }
.bubble-header { font-size: 0.95em; margin-bottom: 3px; }
.bubble-body { font-size: 1.05em; line-height: 1.6; }
.chat-input { border-top: 1px solid #e6eaf1; background: #fff; border-radius: 0 0 18px 18px; }
.bubble-actions button { margin-left: 4px; }
.messages-layout { height: 75vh; background: #fff; border-radius: 18px; box-shadow: 0 2px 16px #163b7c19; }
.conv-list { width: 240px; border-right: 1px solid #e6eaf1; overflow-y: auto; background: #f7f9fb; border-radius: 18px 0 0 18px; }
.conv-item { cursor: pointer; }
.conv-item.active { background: #0d6efd; color: #fff; }
.modal-backdrop-custom { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(30,40,100,0.15); display: flex; align-items: center; justify-content: center; z-index: 1050; }
</style>













