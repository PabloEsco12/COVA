<template>
  <div class="chat-container">
    <div class="chat-header d-flex align-items-center px-3 py-2">
      <i class="bi bi-chat-dots fs-2 text-primary me-3"></i>
      <div>
        <h3 class="mb-0 fw-bold">Messagerie</h3>
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
          :key="msg.id"
          :class="['chat-bubble', msg.sentByMe ? 'sent' : 'received']"
        >
          <div class="bubble-header">
            <span class="fw-bold text-primary">{{ msg.username }}</span>
            <span class="text-muted small ms-2">{{ formatDate(msg.date) }}</span>
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
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'

const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const messagesEnd = ref(null)
const username = localStorage.getItem('username') || 'Moi'

// Fonction de formatage de la date/heure
function formatDate(ts) {
  const d = new Date(ts)
  return d.toLocaleString('fr-BE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

// Récupère les messages
async function fetchMessages() {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:5000/api/messages', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    // Adapter selon le format de réponse réel de l’API
    messages.value = (res.data.messages || []).map(msg => ({
      ...msg,
      sentByMe: msg.sender_email === localStorage.getItem('user_email') // À adapter selon ton API
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

// Envoi d’un message
async function sendMessage() {
  if (!newMessage.value.trim()) return
  const content = newMessage.value
  newMessage.value = ''
  loading.value = true
  try {
    await axios.post('http://localhost:5000/api/messages', {
      content
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    await fetchMessages()
  } catch (e) {
    // Gère l’erreur si besoin
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMessages()
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
</style>