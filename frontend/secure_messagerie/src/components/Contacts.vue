<template>
  <div class="contacts-page">
    <section class="contacts-card">
      <header class="contacts-header">
        <div>
          <h2>Mes contacts</h2>
          <p class="subtitle">Invitez vos interlocuteurs et gérez votre carnet sécurisé.</p>
        </div>
        <button
          type="button"
          class="icon-button"
          :disabled="loading"
          @click="fetchContacts"
        >
          <span aria-hidden="true">⟳</span>
          <span class="sr-only">Rafraîchir</span>
        </button>
      </header>

      <form class="add-form" @submit.prevent="handleAdd">
        <div class="field">
          <label for="contact-email">Adresse e-mail</label>
          <input
            id="contact-email"
            v-model.trim="newEmail"
            type="email"
            placeholder="contact@exemple.com"
            :disabled="adding"
            required
          />
        </div>
        <div class="field">
          <label for="contact-alias">Alias (optionnel)</label>
          <input
            id="contact-alias"
            v-model.trim="newAlias"
            type="text"
            placeholder="Nom affiché"
            :disabled="adding"
          />
        </div>
        <div class="actions">
          <span v-if="addError" class="error-text">{{ addError }}</span>
          <button type="submit" :disabled="adding || !isEmailValid">
            {{ adding ? 'Ajout…' : 'Ajouter' }}
          </button>
        </div>
      </form>

      <div class="list-wrapper">
        <p v-if="loading" class="placeholder">Chargement des contacts…</p>
        <p v-else-if="contacts.length === 0" class="placeholder">
          Aucun contact pour le moment. Ajoutez une adresse pour démarrer.
        </p>
        <ul v-else class="contacts-list">
          <li v-for="contact in contacts" :key="contact.id" class="contact-row">
            <div class="avatar">
              <span>{{ initials(contactAlias(contact) || contactEmail(contact)) }}</span>
            </div>
            <div class="contact-info">
              <h3>{{ contactAlias(contact) || contactEmail(contact) }}</h3>
              <p>{{ contactEmail(contact) }}</p>
            </div>
            <div class="contact-meta">
              <time v-if="contact.created_at" :datetime="contact.created_at">
                Ajouté le {{ formatDate(contact.created_at) }}
              </time>
              <button
                type="button"
                class="link-button"
                :disabled="deletingId === contact.contact_id"
                @click="handleDelete(contact)"
              >
                {{ deletingId === contact.contact_id ? 'Suppression…' : 'Supprimer' }}
              </button>
            </div>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import {
  createContact,
  deleteContact,
  listContacts,
} from '@/services/messagingService'

const contacts = ref([])
const loading = ref(false)
const adding = ref(false)
const addError = ref('')
const newEmail = ref('')
const newAlias = ref('')
const deletingId = ref(null)

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const isEmailValid = computed(() => emailPattern.test(newEmail.value || ''))

function contactAlias(contact) {
  return contact.alias || contact.contact?.display_name || null
}

function contactEmail(contact) {
  return contact.contact?.email || ''
}

function initials(source) {
  if (!source) return 'C'
  const words = source.trim().split(/\s+/)
  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase()
  }
  return (words[0][0] + words[1][0]).toUpperCase()
}

function formatDate(iso) {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('fr-BE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

async function fetchContacts() {
  loading.value = true
  try {
    contacts.value = await listContacts()
  } catch (error) {
    console.error('Unable to load contacts', error)
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!isEmailValid.value || adding.value) return
  adding.value = true
  addError.value = ''
  try {
    const created = await createContact({
      email: newEmail.value,
      alias: newAlias.value || null,
    })
    contacts.value = [created, ...contacts.value]
    newEmail.value = ''
    newAlias.value = ''
  } catch (error) {
    console.error('Unable to add contact', error)
    addError.value =
      error?.response?.data?.detail ||
      "Impossible d'ajouter ce contact."
  } finally {
    adding.value = false
  }
}

async function handleDelete(contact) {
  if (!contact?.contact_id || deletingId.value) return
  deletingId.value = contact.contact_id
  try {
    await deleteContact(contact.contact_id)
    contacts.value = contacts.value.filter(item => item.contact_id !== contact.contact_id)
  } catch (error) {
    console.error('Unable to delete contact', error)
  } finally {
    if (deletingId.value === contact.contact_id) {
      deletingId.value = null
    }
  }
}

onMounted(fetchContacts)
</script>

<style scoped src="../styles/components/Contacts.css"></style>
