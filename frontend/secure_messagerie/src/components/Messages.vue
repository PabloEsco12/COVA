<template>
<div class="messages-layout d-flex">
    <!-- Liste des conversations -->
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
          :class="{active: conv.id === selectedConvId}"
          @click="selectConversation(conv.id)"
        >
          {{ conv.titre }}
        </li>
      </ul>
    </div>

    <!-- Zone de messages -->
    <div class="chat-container flex-grow-1">
      <div class="chat-header d-flex align-items-center px-3 py-2">
        <i class="bi bi-chat-dots fs-2 text-primary me-3"></i>
        <div class="flex-grow-1">
          <h3 class="mb-0 fw-bold">{{ currentConvTitle }}</h3>
          <small class="text-muted">Discussions sécurisées sur COVA</small>
        </div>
        <div class="ms-auto">
          <button class="btn btn-outline-primary btn-sm" @click="refresh">
            <i class="bi bi-arrow-clockwise"></i>
          </button>
        </div>
      </div>


    <div class="chat-messages p-3 flex-grow-1" ref="messagesEnd">
      <div v-if="loading" class="text-center py-5">
        <span class="spinner-border text-primary"></span>
      </div>
      <div v-else-if="messages.length === 0" class="text-center text-muted py-5">
        <i class="bi bi-inbox display-4"></i>
        <div>Aucun message pour le moment</div>
      </div>
      <div v-else>
        <div
          v-for="msg in messages"
           :key="msg.id_msg"
          :class="['chat-bubble', msg.sentByMe ? 'sent' : 'received']"
        >
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
          <div class="bubble-body">{{ msg.content }}</div>
        </div>
      </div>
    </div>

    <form @submit.prevent="sendMessage" class="chat-input px-3 py-2">
      <div class="input-group">
        <input
          v-model="newMessage"
          type="text"
          class="form-control"
          placeholder="Écrire un message…"
          :disabled="loading"
          @keyup.enter="sendMessage"
          autocomplete="off"
        />
        <button class="btn btn-primary" type="submit" :disabled="!newMessage || loading">
          <i class="bi bi-send"></i>
        </button>
      </div>
    </form>
  </div>
  
  <!-- Modal nouvelle conversation -->
  <div v-if="showConvModal" class="modal-backdrop-custom">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content p-3">
        <div class="modal-header">
          <h5 class="modal-title">Nouvelle conversation</h5>
          <button type="button" class="btn-close" @click="showConvModal = false"></button>
        </div>
        <div class="modal-body">
          <input v-model="convTitle" type="text" class="form-control mb-2" placeholder="Titre" />
          <div v-for="c in contacts" :key="c.user_id" class="form-check">
            <input class="form-check-input" type="checkbox" :value="c.user_id" v-model="selectedUsers">
            <label class="form-check-label">{{ c.pseudo }}</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showConvModal = false">Annuler</button>
          <button class="btn btn-primary" @click="createConversation" :disabled="creatingConv">
            <span v-if="creatingConv" class="spinner-border spinner-border-sm"></span>
            <span v-else>Créer</span>
          </button>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'

const conversations = ref([])
const selectedConvId = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const messagesEnd = ref(null)
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

// Fonction de formatage de la date/heure
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

// Récupère les messages d'une conversation
async function fetchMessages() {
    if (!selectedConvId.value) { messages.value = []; return }
  loading.value = true
  try {
    const res = await axios.get(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    // Adapter selon le format de réponse réel de l’API
    messages.value = (res.data || []).map(m => ({
      ...m,
      sentByMe: m.sender_id === userId
    }))
    // Scrolle en bas après chargement
    await nextTick()
    messagesEnd.value.scrollTop = messagesEnd.value.scrollHeight
  } catch (e) {
    messages.value = []
  } finally {
    loading.value = false
  }
}

function refresh() {
  fetchMessages()
}

function selectConversation(id) {
  selectedConvId.value = id
  const conv = conversations.value.find(c => c.id === id)
  currentConvTitle.value = conv ? conv.titre : 'Messagerie'
}


// Envoi d’un message
async function sendMessage() {
  if (!newMessage.value.trim() || !selectedConvId.value) return
  const content = newMessage.value
  newMessage.value = ''
  loading.value = true
  try {
    await axios.post(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/`, {
      contenu_chiffre: content
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    await fetchMessages()
  } catch (e) {
  } finally {
    loading.value = false
  }
}

function startEdit(msg) {
  editingId.value = msg.id_msg
  editContent.value = msg.contenu_chiffre
}

async function confirmEdit() {
  if (!editingId.value) return
  try {
    await axios.put(`http://localhost:5000/api/conversations/${selectedConvId.value}/messages/${editingId.value}`, {
      contenu_chiffre: editContent.value
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
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
  } catch {
    contacts.value = []
  }
}

function openConvModal() {
  selectedUsers.value = []
  convTitle.value = ''
  fetchContacts()
  showConvModal.value = true
}

async function createConversation() {
  if (!convTitle.value) return
  creatingConv.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/conversations/', {
      titre: convTitle.value,
      participants: selectedUsers.value,
      is_group: selectedUsers.value.length > 1
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
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



onMounted(async () => {
  await fetchConversations()
    if (selectedConvId.value) {
    selectConversation(selectedConvId.value)
  }
  await fetchMessages()
})

watch(selectedConvId, async (val) => {
  if (val) {
    selectConversation(val)
    await fetchMessages()
  }
})
</script>

<style scoped>
.chat-container {
  background: #f7f9fb;
  border-radius: 18px;
  box-shadow: 0 2px 16px #163b7c19;
  height: 75vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  border-bottom: 1px solid #e6eaf1;
  background: #fff;
  border-radius: 18px 18px 0 0;
}

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  background: #f7f9fb;
}

.chat-bubble {
  margin-bottom: 14px;
  max-width: 78%;
  padding: 0.8rem 1.2rem;
  border-radius: 18px;
  word-break: break-word;
  position: relative;
  background: #fff;
  box-shadow: 0 2px 8px #163b7c11;
}
.chat-bubble.sent {
  background: linear-gradient(120deg, #2157d3 60%, #1959c2 100%);
  color: #fff;
  margin-left: auto;
  text-align: right;
}
.chat-bubble.received {
  background: #fff;
  color: #2d3245;
  margin-right: auto;
  text-align: left;
}
.bubble-header {
  font-size: 0.95em;
  margin-bottom: 3px;
}
.bubble-body {
  font-size: 1.11em;
  line-height: 1.7;
}
.chat-input {
  border-top: 1px solid #e6eaf1;
  background: #fff;
  border-radius: 0 0 18px 18px;
}
.bubble-actions button {
  margin-left: 4px;
}

.messages-layout {
  height: 75vh;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 2px 16px #163b7c19;
}

.conv-list {
  width: 220px;
  border-right: 1px solid #e6eaf1;
  overflow-y: auto;
  background: #f7f9fb;
  border-radius: 18px 0 0 18px;
}

.conv-item {
  cursor: pointer;
}
.conv-item.active {
  background: #0d6efd;
  color: #fff;
}

.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30,40,100,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
</style>