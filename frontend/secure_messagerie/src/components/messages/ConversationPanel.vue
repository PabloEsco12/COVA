<!--
  ===== Component Header =====
  Component: ConversationPanel
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Panneau principal des messages (header, liste, composer).
-->
<template>
  <div v-if="show && selectedConversation" class="msg-panel">
    <div class="msg-panel__header">
      <div>
        <p class="msg-panel__eyebrow">Conversation</p>
        <h4>{{ selectedConversation.displayName }}</h4>
        <p class="msg-panel__subtitle" v-if="selectedConversation.topic">{{ selectedConversation.topic }}</p>
      </div>
      <button type="button" class="msg-panel__close" @click="closeConversationPanel" aria-label="Fermer le panneau">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>
    <p class="msg-panel__hint">
      Gérez les métadonnées, les invitations et les membres de ce canal sécurisé.
    </p>
    <dl class="msg-panel__meta">
      <div>
        <dt>Identifiant</dt>
        <dd><code>{{ selectedConversation.id }}</code></dd>
      </div>
      <div>
        <dt>Créée le</dt>
        <dd>{{ formatAbsolute(selectedConversation.createdAt) }}</dd>
      </div>
      <div>
        <dt>Propriétaires</dt>
        <dd>{{ conversationOwnerSummary }}</dd>
      </div>
    </dl>
    <p v-if="conversationInfoError" class="msg-alert">{{ conversationInfoError }}</p>
    <div
      v-if="conversationInfoNotice"
      class="alert alert-success msg-panel__notice"
      role="status"
    >
      {{ conversationInfoNotice }}
    </div>
    <form class="msg-panel__section" @submit.prevent="saveConversationSettings">
      <div class="mb-3">
        <label class="form-label">Titre</label>
        <input v-model.trim="conversationForm.title" type="text" class="form-control" placeholder="Nom interne de la conversation" maxlength="160" />
        <p class="msg-panel__hint">
          Visible dans la colonne de gauche et dans les notifications.
        </p>
      </div>
      <div class="mb-3">
        <label class="form-label">Sujet</label>
        <textarea v-model.trim="conversationForm.topic" class="form-control" rows="2" placeholder="Contexte ou consignes"></textarea>
        <p class="msg-panel__hint">
          Partagez un rappel ou une consigne qui s'affiche dans ce panneau.
        </p>
      </div>
      <label class="form-check form-switch mb-3">
        <input v-model="conversationForm.archived" class="form-check-input" type="checkbox" />
        <span class="form-check-label">Conversation archivée</span>
      </label>
      <small class="msg-panel__hint text-muted">
        Archivés, les échanges restent consultables mais sont masqués des vues actives.
      </small>
      <div class="d-flex gap-2">
        <button class="btn btn-primary flex-grow-1" type="submit" :disabled="savingConversation">
          <span v-if="savingConversation" class="spinner-border spinner-border-sm me-2"></span>
          Enregistrer
        </button>
        <button class="btn btn-outline-secondary" type="button" @click="closeConversationPanel">Fermer</button>
      </div>
    </form>
    <button
      v-if="canManageConversation"
      class="btn btn-danger w-100 mb-2"
      type="button"
      @click="openDeleteConfirm"
      :disabled="deletingConversation"
      title="Supprimer définitivement cette conversation"
    >
      <span v-if="deletingConversation" class="spinner-border spinner-border-sm me-2"></span>
      Supprimer la conversation
    </button>
    <div v-if="showDeleteConfirm" class="msg-panel__confirm">
      <h6>Supprimer définitivement ?</h6>
      <p class="mb-2">
        Tous les messages, pièces jointes et journaux de cette conversation seront effacés pour tous les participants.
        Cette action est irréversible.
      </p>
      <div class="d-flex flex-wrap gap-2">
        <button class="btn btn-danger flex-grow-1" type="button" @click="deleteCurrentConversation" :disabled="deletingConversation">
          <span v-if="deletingConversation" class="spinner-border spinner-border-sm me-2"></span>
          Oui, supprimer
        </button>
        <button class="btn btn-outline-secondary flex-grow-1" type="button" @click="closeDeleteConfirm" :disabled="deletingConversation">
          Annuler
        </button>
      </div>
    </div>
    <button
      class="btn btn-outline-danger w-100 mb-3"
      type="button"
      @click="leaveCurrentConversation"
      :disabled="leavingConversation"
      title="Se retirer et ne plus recevoir les messages de ce canal"
    >
      <span v-if="leavingConversation" class="spinner-border spinner-border-sm me-2"></span>
      Quitter la conversation
    </button>
    <small class="msg-panel__hint text-muted">
      Lorsque vous êtes le dernier propriétaire actif, un membre actif est automatiquement promu avant votre départ.
    </small>
    <section v-if="canManageConversation" class="msg-panel__section">
      <div class="msg-panel__section-header">
        <h5>Invitations</h5>
        <span v-if="loadingInvites" class="msg-panel__pill">Chargement</span>
      </div>
      <p class="msg-panel__hint">
        Créez des accès temporaires en précisant le rôle souhaité et la durée de validité.
      </p>
      <form class="msg-panel__invite-form" @submit.prevent="submitInvite">
        <input
          v-model.trim="inviteForm.email"
          type="email"
          class="form-control"
          placeholder="Adresse e-mail professionnelle"
          required
        />
        <div class="msg-panel__invite-row">
          <select v-model="inviteForm.role" class="form-select">
            <option v-for="role in conversationRoles" :key="role.value" :value="role.value">
              {{ role.label }}
            </option>
          </select>
          <input
            v-model.number="inviteForm.expiresInHours"
            type="number"
            class="form-control"
            min="1"
            max="336"
            placeholder="Durée (h)"
          />
        </div>
        <button class="btn btn-secondary w-100" type="submit" :disabled="inviteBusy">
          <span v-if="inviteBusy" class="spinner-border spinner-border-sm me-2"></span>
          Générer une invitation
        </button>
      </form>
      <ul class="msg-panel__list">
        <li v-for="invite in invites" :key="invite.id" class="msg-panel__list-item">
          <div>
            <strong>{{ invite.email }}</strong>
            <p class="small mb-0 text-muted">
              {{ roleLabel(member.role) }}
              <span class="msg-presence-pill" :class="memberPresence(member.userId || member.id).status">
                {{ memberPresenceText(member.userId || member.id) }}
              </span>
              <span v-if="member.state !== 'active'"> · {{ member.state }}</span>
              <span v-if="member.mutedUntil" class="msg-panel__pill muted">
                Sourdine {{ formatAbsolute(member.mutedUntil) }}
              </span>
            </p>
          </div>
          <button
            class="btn btn-link text-danger p-0"
            type="button"
            @click="revokeInvite(invite.id)"
            :disabled="inviteRevokeBusy[invite.id]"
          >
            Révoquer
          </button>
        </li>
        <li v-if="!invites.length && !loadingInvites" class="text-muted small">Aucune invitation active.</li>
      </ul>
    </section>
    <section v-if="selectedConversation.members?.length" class="msg-panel__section">
      <div class="msg-panel__section-header">
        <h5>Membres</h5>
        <span class="msg-panel__pill">{{ selectedConversation.members.length }}</span>
      </div>
      <p class="msg-panel__hint">
        Ajustez les rôles, activer une sourdine temporaire ou retirer un collaborateur.
      </p>
      <ul class="msg-panel__list">
        <li v-for="member in selectedConversation.members" :key="member.id" class="msg-panel__member">
          <div class="msg-panel__member-info">
            <div class="msg-panel__member-header">
              <div class="msg-panel__avatar">{{ (member.displayName || member.email || 'M')[0] }}</div>
              <div>
                <strong>{{ member.displayName || member.email }}</strong>
                <p class="small mb-0 text-muted">
                  {{ roleLabel(member.role) }}
                  <span v-if="member.state !== 'active'"> · {{ member.state }}</span>
                </p>
              </div>
            </div>
            <p v-if="member.email" class="small text-muted mb-1">{{ member.email }}</p>
            <span v-if="member.mutedUntil" class="msg-panel__pill muted">
              Sourdine {{ formatAbsolute(member.mutedUntil) }}
            </span>
          </div>
          <div
            v-if="canManageConversation && (member.userId || member.id) !== String(currentUserId || '')"
            class="msg-panel__member-actions"
          >
            <label class="form-label small text-muted mb-1">Rôle</label>
            <select
              class="form-select form-select-sm"
              :value="member.role"
              @change="updateMemberRole(member, $event.target.value)"
              :disabled="memberBusy[member.id]"
            >
              <option v-for="role in conversationRoles" :key="`${member.id}-${role.value}`" :value="role.value">
                {{ role.label }}
              </option>
            </select>
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm w-100"
              @click="member.mutedUntil ? unmuteMember(member) : muteMember(member)"
              :disabled="memberBusy[member.id]"
            >
              {{ member.mutedUntil ? 'Réactiver' : 'Mettre en sourdine 1h' }}
            </button>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
// ===== Props et etat parent =====
const props = defineProps({
  show: Boolean,
  selectedConversation: Object,
  conversationOwnerSummary: String,
  conversationInfoError: String,
  conversationInfoNotice: String,
  conversationForm: Object,
  savingConversation: Boolean,
  leavingConversation: Boolean,
  showDeleteConfirm: Boolean,
  deletingConversation: Boolean,
  loadingInvites: Boolean,
  invites: {
    type: Array,
    default: () => [],
  },
  inviteForm: Object,
  inviteBusy: Boolean,
  inviteRevokeBusy: {
    type: Object,
    default: () => ({}),
  },
  memberBusy: {
    type: Object,
    default: () => ({}),
  },
  canManageConversation: Boolean,
  currentUserId: [String, Number],
  conversationRoles: {
    type: Array,
    default: () => [],
  },
  formatAbsolute: {
    type: Function,
    required: true,
  },
  roleLabel: {
    type: Function,
    required: true,
  },
  memberPresence: {
    type: Function,
    required: true,
  },
  memberPresenceText: {
    type: Function,
    required: true,
  },
  closeConversationPanel: {
    type: Function,
    required: true,
  },
  saveConversationSettings: {
    type: Function,
    required: true,
  },
  leaveCurrentConversation: {
    type: Function,
    required: true,
  },
  openDeleteConfirm: {
    type: Function,
    required: true,
  },
  closeDeleteConfirm: {
    type: Function,
    required: true,
  },
  deleteCurrentConversation: {
    type: Function,
    required: true,
  },
  submitInvite: {
    type: Function,
    required: true,
  },
  revokeInvite: {
    type: Function,
    required: true,
  },
  updateMemberRole: {
    type: Function,
    required: true,
  },
  muteMember: {
    type: Function,
    required: true,
  },
  unmuteMember: {
    type: Function,
    required: true,
  },
  removeMember: {
    type: Function,
    required: true,
  },
})
</script>
