<template>

  <div class="msg-shell">
    <transition-group name="msg-toast" tag="div" class="msg-toast-stack">
      <article
        v-for="toast in messageToasts"
        :key="toast.id"
        class="msg-toast"
        @click="openToastConversation(toast)"
      >
        <div class="msg-toast__content">
          <p class="msg-toast__title">{{ toast.title }}</p>
          <p class="msg-toast__body">{{ toast.body }}</p>
          <small>{{ formatTime(toast.createdAt) }}</small>
        </div>
        <button
          type="button"
          class="msg-toast__close"
          @click.stop="dismissToast(toast.id)"
          aria-label="Fermer la notification"
        >
          <i class="bi bi-x-lg"></i>
        </button>
      </article>
    </transition-group>

    

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

            <div v-if="!selectedConversation" class="msg-empty">
        <h3>Messagerie sécurisée</h3>
        <p>Choisissez une conversation ou créez-en une nouvelle avec vos contacts vérifiés.</p>
        <button class="btn btn-primary" type="button" @click="goToNewConversation">Nouvelle conversation</button>
      </div>
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
        <div v-if="showSearchPanel" class="msg-search-panel">
          <form class="msg-search-panel__form" @submit.prevent="performMessageSearch">
            <input
              v-model.trim="messageSearch.query"
              type="search"
              class="form-control"
              placeholder="Rechercher dans cette conversation"
            />
            <button class="btn btn-secondary btn-sm" type="submit" :disabled="messageSearch.loading">
              <span v-if="messageSearch.loading" class="spinner-border spinner-border-sm me-2"></span>
              Rechercher
            </button>
            <button type="button" class="btn btn-link btn-sm" @click="closeSearchPanel">Fermer</button>
          </form>
          <p v-if="messageSearch.error" class="msg-alert">{{ messageSearch.error }}</p>
          <ul class="msg-search-results">
            <li
              v-for="result in messageSearch.results"
              :key="result.id"
              class="msg-search-results__item"
            >
              <div>
                <p class="msg-search__author">{{ result.displayName }}</p>
                <p class="msg-search__excerpt">{{ messagePreviewText(result) }}</p>
                <small class="text-muted">{{ formatAbsolute(result.createdAt) }}</small>
              </div>
              <button type="button" class="btn btn-link p-0" @click="jumpToSearchResult(result)">Afficher</button>
            </li>
            <li
              v-if="messageSearch.executed && !messageSearch.loading && !messageSearch.results.length"
              class="text-muted small"
            >
              Aucun message trouvé.
            </li>
          </ul>
        </div>
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

        <div
          v-if="composerBlockedInfo"
          class="msg-composer msg-composer--disabled"
        >
          <div class="msg-blocked-banner__icon">
            <i :class="composerBlockedInfo.state === 'blocked_by_other' ? 'bi bi-shield-lock-fill' : 'bi bi-shield-check'" aria-hidden="true"></i>
          </div>
          <div class="msg-blocked-banner__body">
            <p class="mb-1 fw-semibold">{{ composerBlockedInfo.title }}</p>
            <p class="mb-0 text-muted">{{ composerBlockedInfo.message }}</p>
          </div>
          <router-link to="/dashboard/contacts" class="btn btn-outline-primary btn-sm">
            Gérer les contacts
          </router-link>
        </div>

        <form v-else class="msg-composer" @submit.prevent="sendMessage">
          <div class="msg-composer__pickers">
            <div v-if="showPicker" class="msg-picker" role="menu" aria-label="Choisir un contenu">
              <div class="msg-picker__header">
                <div class="msg-picker__tabs">
                  <button type="button" :class="{ active: pickerMode === 'emoji' }" @click="setPickerMode('emoji')">Emoji</button>
                  <button type="button" :class="{ active: pickerMode === 'gif' }" @click="setPickerMode('gif')">GIF</button>
                </div>
                <input
                  v-if="pickerMode === 'emoji'"
                  v-model.trim="emojiSearch"
                  type="search"
                  class="msg-picker__search"
                  placeholder="Rechercher un emoji"
                />
                <input
                  v-else-if="gifSearchAvailable"
                  v-model.trim="gifSearch"
                  type="search"
                  class="msg-picker__search"
                  placeholder="Rechercher un GIF"
                />
                <p v-else class="msg-picker__hint">Bibliothèque locale de GIFs prête à l'emploi.</p>
              </div>
              <div class="msg-picker__body" v-if="pickerMode === 'emoji'">
                <div
                  v-for="section in filteredEmojiSections"
                  :key="section.id"
                  class="msg-picker__section"
                >
                  <p class="msg-picker__section-title">{{ section.label }}</p>
                  <div class="msg-picker__grid">
                    <button
                      type="button"
                      v-for="emoji in section.items"
                      :key="`${section.id}-${emoji}`"
                      @click="addEmoji(emoji)"
                    >
                      {{ emoji }}
                    </button>
                  </div>
                </div>
              </div>
              <div class="msg-picker__body msg-picker__body--gifs" v-else>
                <button type="button" v-for="gif in displayedGifs" :key="gif.url" @click="insertGif(gif)">
                  <img :src="gif.preview || gif.url" :alt="gif.label" />
                  <span>{{ gif.label }}</span>
                </button>
                <p v-if="gifError && gifSearchAvailable && !loadingGifs" class="msg-picker__error">{{ gifError }}</p>
                <div v-if="loadingGifs" class="msg-picker__loading">
                  <span class="spinner-border spinner-border-sm me-2"></span>
                  Chargementâ?,?¦
                </div>
              </div>
            </div>
          </div>
          <input ref="attachmentInput" class="visually-hidden" type="file" multiple @change="onAttachmentChange" />
          <textarea
            v-model="messageInput"
            class="form-control"
            rows="2"
            placeholder="Ecrire un message sécurisé."
            :disabled="sending"
            @keydown.enter.exact.prevent="sendMessage"
            @input="onComposerInput"
            @blur="handleComposerBlur"
          ></textarea>
          <div v-if="pendingAttachments.length && !isEditingMessage" class="msg-composer__attachments">
            <article v-for="attachment in pendingAttachments" :key="attachment.id" class="msg-composer__attachment">
              <div>
                <strong>{{ attachment.name }}</strong>
                <p class="small mb-0 text-muted">
                  {{ formatFileSize(attachment.size) }}
                  <span v-if="attachment.status === 'uploading'"> ?,· {{ attachment.progress || 0 }}%</span>
                  <span v-if="attachment.status === 'error'" class="text-danger"> ?,· {{ attachment.error }}</span>
                </p>
              </div>
              <div class="msg-composer__attachment-actions">
                <span v-if="attachment.status === 'uploading'" class="msg-panel__pill">Envoiâ?,?¦</span>
                <span v-else-if="attachment.status === 'ready'" class="msg-panel__pill ok">Prête</span>
                <button type="button" class="btn btn-link p-0" @click="removeAttachment(attachment.id)">Retirer</button>
              </div>
            </article>
          </div>
          <p v-if="attachmentError" class="msg-alert mb-2">{{ attachmentError }}</p>
          <div v-if="hasComposerContext" class="msg-composer__context">
            <div>
              <template v-if="isEditingMessage">
                <strong>Modification du message</strong>
              </template>
              <template v-else-if="composerState.replyTo">
                <strong>Réponse à {{ composerState.replyTo.displayName || composerState.replyTo.authorDisplayName || 'Participant' }}</strong>
                <p class="small mb-0 text-muted">
                  {{ messagePreviewText(composerState.replyTo) }}
                </p>
              </template>
              <template v-else-if="composerState.forwardFrom">
                <strong>Transfert</strong>
                <p class="small mb-0 text-muted">
                  {{ messagePreviewText(composerState.forwardFrom) }}
                </p>
              </template>
            </div>
            <button type="button" class="btn btn-link p-0" @click="cancelComposerContext">Annuler</button>
          </div>
          <p v-if="typingIndicatorText" class="msg-typing-indicator">
            <i class="bi bi-pencil" aria-hidden="true"></i>
            <span>{{ typingIndicatorText }}</span>
          </p>
          <div class="msg-composer__footer">
            <div class="msg-composer__left">
              <div class="msg-composer__actions">
                <button
                  type="button"
                  class="msg-icon-btn"
                  @click="triggerAttachmentPicker"
                  :disabled="hasAttachmentInProgress || isEditingMessage"
                  aria-label="Ajouter une pièce jointe"
                >
                  <i class="bi bi-paperclip"></i>
                </button>
                <button type="button" class="msg-icon-btn primary" @click="togglePicker" aria-label="Emoji et GIF">
                  <i class="bi bi-emoji-smile"></i>
                </button>
              </div>
              <small>{{ messageInput.length }}/2000</small>
            </div>
            <button class="btn btn-primary" type="submit" :disabled="!canSend || sending">

              <span v-if="sending" class="spinner-border spinner-border-sm me-2"></span>

              Envoyer

            </button>

          </div>

        </form>

        <CustomModal v-model="deleteDialog.visible">
          <template #title>
            <i class="bi bi-trash me-2"></i>Supprimer le message
          </template>
          <p class="mb-2">
            Cette action retirera définitivement ce message pour tous les participants de la conversation.
          </p>
          <div v-if="deleteDialogPreview" class="alert alert-warning py-2 px-3 mb-3">
            <strong>Aperçu&nbsp;:</strong>
            <span class="ms-1">{{ deleteDialogPreview }}</span>
          </div>
          <div v-if="deleteDialog.error" class="alert alert-danger">
            {{ deleteDialog.error }}
          </div>
          <template #footer>
            <button class="btn btn-outline-secondary" type="button" :disabled="deleteDialog.loading" @click="closeDeleteDialog">
              Annuler
            </button>
            <button class="btn btn-danger" type="button" :disabled="deleteDialog.loading" @click="performDeleteMessage">
              <span v-if="deleteDialog.loading" class="spinner-border spinner-border-sm me-2"></span>
              Supprimer pour tous
            </button>
          </template>
        </CustomModal>

        <div
          v-if="callState.status !== 'idle'"
          class="call-overlay"
          role="dialog"
          aria-modal="true"
          :aria-label="callStatusLabel"
        >
          <div class="call-panel">
            <header class="call-panel__header">
              <div>
                <p class="call-panel__eyebrow">{{ callState.kind === 'video' ? 'Appel vidéo' : 'Appel audio' }}</p>
                <h4>{{ callStatusLabel }}</h4>
                <p class="call-panel__subtitle">{{ remoteDisplayName }}</p>
              </div>
            </header>
            <div
              class="call-video"
              :class="{ 'call-video--audio': callState.kind !== 'video' }"
            >
              <div class="call-remote">
                <template v-if="callState.kind === 'video'">
                  <video
                    ref="remoteVideoRef"
                    autoplay
                    playsinline
                    class="call-video__stream"
                    :class="{ 'call-video__stream--hidden': !callState.remoteStream }"
                  ></video>
                </template>
                <div v-else class="call-audio-placeholder">
                  <i class="bi bi-person-fill"></i>
                </div>
                <p class="call-remote__label">{{ remoteDisplayName }}</p>
              </div>
              <div v-if="callState.kind === 'video'" class="call-local">
                <video
                  ref="localVideoRef"
                  autoplay
                  muted
                  playsinline
                  class="call-video__stream call-video__stream--local"
                ></video>
                <p class="call-local__label">Vous</p>
              </div>
            </div>
            <p v-if="callState.error" class="msg-alert mt-2">{{ callState.error }}</p>
            <div class="call-controls">
              <template v-if="callState.status === 'incoming'">
                <button type="button" class="btn btn-success" @click="acceptIncomingCall">
                  <i class="bi bi-telephone-inbound-fill me-1"></i>
                  Répondre
                </button>
                <button type="button" class="btn btn-secondary" @click="rejectIncomingCall">
                  Refuser
                </button>
              </template>
              <template v-else-if="callState.status === 'outgoing'">
                <button type="button" class="btn btn-secondary" @click="cancelOutgoingCall">
                  Annuler l'appel
                </button>
              </template>
              <div v-if="callState.status === 'connected'" class="call-controls__toggles">
                <button
                  type="button"
                  class="btn"
                  :class="{ 'is-muted': !callControls.micEnabled }"
                  @click="toggleMicrophone"
                >
                  <i :class="callControls.micEnabled ? 'bi bi-mic-fill' : 'bi bi-mic-mute-fill'"></i>
                </button>
                <button
                  v-if="callState.kind === 'video'"
                  type="button"
                  class="btn"
                  :class="{ 'is-muted': !callControls.cameraEnabled }"
                  @click="toggleCamera"
                >
                  <i :class="callControls.cameraEnabled ? 'bi bi-camera-video-fill' : 'bi bi-camera-video-off-fill'"></i>
                </button>
              </div>
              <button
                v-if="callState.status !== 'incoming'"
                type="button"
                class="btn btn-danger"
                @click="hangupCall"
              >
                <i class="bi bi-telephone-x-fill me-1"></i>
                Raccrocher
              </button>
            </div>
          </div>
        </div>

      </template>

    </section>
  </div>
  <div v-if="showConversationPanel && selectedConversation" class="msg-panel">
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
          <div>
            <strong>{{ member.displayName || member.email }}</strong>
            <p class="small mb-0 text-muted">
              {{ roleLabel(member.role) }}
              <span v-if="member.state !== 'active'"> ?,· {{ member.state }}</span>
              <span v-if="member.mutedUntil" class="msg-panel__pill muted">
                Sourdine {{ formatAbsolute(member.mutedUntil) }}
              </span>
            </p>
          </div>
          <div
            v-if="canManageConversation && (member.userId || member.id) !== String(currentUserId || '')"
            class="msg-panel__member-actions"
          >
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
              class="btn btn-link p-0"
              @click="member.mutedUntil ? unmuteMember(member) : muteMember(member)"
              :disabled="memberBusy[member.id]"
            >
              {{ member.mutedUntil ? 'Réactiver' : 'Sourdine 1h' }}
            </button>
            <button
              type="button"
              class="btn btn-link text-danger p-0"
              @click="removeMember(member)"
              :disabled="memberBusy[member.id]"
            >
              Retirer
            </button>
          </div>
        </li>
      </ul>
    </section>
  </div>

  <div
    v-if="forwardPicker.open"
    class="forward-picker__backdrop"
    role="dialog"
    aria-modal="true"
    aria-label="Choisir la destination du transfert"
    @click="cancelForwardSelection"
  >
    <div class="forward-picker__panel" @click.stop>
      <header class="forward-picker__header">
        <p class="forward-picker__eyebrow">Transférer ce message</p>
        <div class="forward-picker__preview">
          <strong class="forward-picker__preview-author">
            {{ forwardPicker.message?.displayName || 'Message sélectionné' }}
          </strong>
          <p class="forward-picker__preview-body">
            {{ messagePreviewText(forwardPicker.message) }}
          </p>
        </div>
      </header>
      <div class="forward-picker__search">
        <input
          ref="forwardPickerInput"
          v-model.trim="forwardPicker.query"
          type="search"
          class="form-control"
          placeholder="Rechercher un contact ou une conversation"
        />
      </div>
      <div class="forward-picker__list" role="listbox">
        <button
          v-for="target in forwardPickerTargets"
          :key="`forward-target-${target.id}`"
          type="button"
          class="forward-picker__item"
          @click="confirmForwardTarget(target.id)"
        >
          <div class="forward-picker__item-main">
            <span class="forward-picker__item-title">{{ target.displayName }}</span>
            <span v-if="target.id === selectedConversationId" class="forward-picker__badge">Actuelle</span>
          </div>
          <p class="forward-picker__item-subtitle">
            {{ target.participantsLabel || 'Conversation sécurisée' }}
          </p>
        </button>
        <p v-if="!forwardPickerTargets.length" class="forward-picker__empty">
          Aucune conversation ne correspond à votre recherche.
        </p>
      </div>
      <div class="forward-picker__actions">
        <router-link class="btn btn-outline-primary flex-grow-1" to="/dashboard/messages/new" @click="cancelForwardSelection">
          Nouvelle conversation
        </router-link>
        <button type="button" class="btn btn-light" @click="cancelForwardSelection">Annuler</button>
      </div>
    </div>
  </div>
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
  updateConversation,
  leaveConversation,
  updateConversationMember,
  listConversationInvites,
  createConversationInvite,
  revokeConversationInvite,
} from '@/services/conversations'
import { fetchGifs, hasGifApiSupport } from '@/services/media'
import { emojiSections, emojiCatalog, defaultGifLibrary } from '@/utils/reactions'
import { detectGifLinks, stripGifLinks } from '@/utils/messageContent'
import { broadcastProfileUpdate, normalizeAvatarUrl } from '@/utils/profile'
import ConversationSidebar from '@/components/messages/ConversationSidebar.vue'
import ChatHeader from '@/components/messages/ChatHeader.vue'
import MessageList from '@/components/messages/MessageList.vue'
import AvailabilityMenu from '@/components/messages/AvailabilityMenu.vue'
import CustomModal from '@/components/ui/CustomModal.vue'


const gifLibrary = defaultGifLibrary
const PRESENCE_STALE_MS = 60000


const STATUS_LABELS = {
  online: 'En ligne',
  available: 'Disponible',
  meeting: 'En réunion',
  busy: 'Occupé',
  dnd: 'Ne pas déranger',
  away: 'Absent',
  offline: 'Hors ligne',
}

const STATUS_PRESETS = {
  available: { label: 'Disponible', message: 'Disponible' },
  away: { label: 'Absent', message: 'Absent' },
  meeting: { label: 'En réunion', message: 'En réunion' },
  busy: { label: 'Occupé', message: 'Occupé' },
  dnd: { label: 'Ne pas déranger', message: 'Ne pas déranger' },
  offline: { label: 'Hors ligne', message: '' },
}

const availabilityOptions = [
  { value: 'available', label: 'Disponible' },
  { value: 'away', label: 'Absent' },
  { value: 'meeting', label: 'En réunion' },
  { value: 'busy', label: 'Occupé' },
  { value: 'dnd', label: 'Ne pas déranger' },
  { value: 'offline', label: 'Hors ligne' },
]

const storedStatusMessage = (() => {
  try {
    return localStorage.getItem('status_message') || ''
  } catch {
    return ''
  }
})()
const myAvailability = ref(resolveAvailabilityFromStatus(storedStatusMessage))
const conversationPresence = reactive({})
const conversationPresenceSource = reactive({})
const deleteDialog = reactive({
  visible: false,
  message: null,
  loading: false,
  error: '',
})
const deleteDialogPreview = computed(() =>
  deleteDialog.message ? messagePreviewText(deleteDialog.message) : '',
)

const conversations = ref([])

watch(
  conversations,
  (list) => {
    list.forEach((conv) => {
      refreshManualPresenceForConversation(conv)
    })
  },
  { deep: true, immediate: true },
)

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
const showConversationPanel = ref(false)
const conversationForm = reactive({ title: '', topic: '', archived: false })
const savingConversation = ref(false)
const conversationInfoError = ref('')
const conversationInfoNotice = ref('')
let conversationNoticeTimer = null
const presenceSnapshot = ref({ users: [], timestamp: null })
const typingTimestamps = reactive({})
const typingUsers = ref([])
let typingCleanupTimer = null
const invites = ref([])
const loadingInvites = ref(false)
const inviteForm = reactive({ email: '', role: 'member', expiresInHours: 72 })
const inviteBusy = ref(false)
const inviteRevokeBusy = reactive({})
const memberBusy = reactive({})
const leavingConversation = ref(false)
const attachmentInput = ref(null)
const pendingAttachments = ref([])
const attachmentError = ref('')
const composerState = reactive({
  mode: 'new', // new | reply | forward | edit
  targetMessageId: null,
  replyTo: null,
  forwardFrom: null,
})
const forwardPicker = reactive({
  open: false,
  message: null,
  query: '',
})
const forwardPickerInput = ref(null)
const pagination = reactive({
  beforeCursor: null,
  afterCursor: null,
  hasMoreBefore: false,
  hasMoreAfter: false,
})
const loadingOlderMessages = ref(false)
const suppressAutoScroll = ref(false)
const selectedConversationId = ref(null)
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

const messageError = ref('')

const messageInput = ref('')

const sending = ref(false)

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

const showPicker = ref(false)
const pickerMode = ref('emoji')
const emojiSearch = ref('')
const gifSearch = ref('')
const gifResults = ref(gifLibrary.slice())
const loadingGifs = ref(false)
const gifError = ref('')
const gifSearchAvailable = hasGifApiSupport()
const messageToasts = ref([])
const toastTimers = new Map()
const optimisticMessageIds = new Set()
const notificationDedupSet = new Set()
let notificationPermissionRequestPending = false
const browserNotificationsEnabled = ref(readBrowserNotificationPreference())
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i


const socketRef = ref(null)
const localVideoRef = ref(null)
const remoteVideoRef = ref(null)
const callState = reactive({
  status: 'idle',
  callId: null,
  kind: 'audio',
  remoteUserId: null,
  incomingOffer: null,
  initiator: false,
  error: '',
  localStream: null,
  remoteStream: null,
})
const callControls = reactive({
  micEnabled: true,
  cameraEnabled: true,
})
let peerConnection = null
const rtcConfig = {
  iceServers: [
    { urls: ['stun:stun.l.google.com:19302', 'stun:stun1.l.google.com:19302'] },
  ],
}
const pendingIceCandidates = []
const localTypingState = reactive({ active: false, timer: null })
const LOCAL_TYPING_IDLE_MS = 3500
const REMOTE_TYPING_STALE_MS = 6000

const connectionStatus = ref('idle')
const realtimeConversationId = ref(null)



let copyTimer = null
let gifSearchTimer = null


const route = useRoute()

const router = useRouter()

const messageListRef = ref(null)



const currentUserId = ref(localStorage.getItem('user_id') || null)
const authToken = ref(localStorage.getItem('access_token') || null)
const notificationsStream = useNotificationsStream({
  token: authToken.value,
  onNotification: (payload) => processNotificationPayload(payload, 'stream'),
})


function isValidUuid(value) {
  return typeof value === 'string' && UUID_PATTERN.test(value)
}

function readBrowserNotificationPreference() {
  try {
    return localStorage.getItem('notif_browser') === '1'
  } catch {
    return false
  }
}

function syncBrowserNotificationPreference() {
  browserNotificationsEnabled.value = readBrowserNotificationPreference()
}

function handleBrowserPrefStorage(event) {
  if (event?.key === 'notif_browser') {
    syncBrowserNotificationPreference()
  }
}

function handleBrowserPrefBroadcast(event) {
  if (event?.detail && typeof event.detail.enabled === 'boolean') {
    browserNotificationsEnabled.value = event.detail.enabled
  }
}

function computeInitials(label = '') {
  if (!label) return 'C'
  const tokens = String(label)
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!tokens.length) return 'C'
  const first = tokens[0][0] || ''
  const second = tokens.length > 1 ? tokens[tokens.length - 1][0] : tokens[0][1] || ''
  const initials = (first + (second || '')).toUpperCase()
  return initials || 'C'
}

function normalizeMember(member) {
  if (!member) return null
  const userId = member.user_id || member.userId || member.contact_user_id || null
  const membershipId = member.id || member.member_id || member.membership_id || userId
  if (!membershipId) return null
  const displayName = member.display_name || member.email || 'Membre'
  const avatarUrl = normalizeAvatarUrl(member.avatar_url || null, { baseUrl: backendBase })
  return {
    id: String(membershipId),
    membershipId: membershipId ? String(membershipId) : null,
    userId: userId ? String(userId) : null,
    role: member.role || 'member',
    state: member.state || 'active',
    joinedAt: member.joined_at ? new Date(member.joined_at) : null,
    mutedUntil: member.muted_until ? new Date(member.muted_until) : null,
    displayName,
    email: member.email || '',
    avatarUrl,
    initials: computeInitials(displayName),
    statusMessage: member.status_message || '',
  }
}

function normalizeConversation(payload) {
  if (!payload) return null
  const members = Array.isArray(payload.members)
    ? payload.members.map((member) => normalizeMember(member)).filter(Boolean)
    : []
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  const activeParticipants = members.filter((member) => {
    const userKey = memberUserId(member)
    return member.state === 'active' && (!selfId || userKey !== selfId)
  })
  const createdAt = payload.created_at ? new Date(payload.created_at) : new Date()
  let displayName = payload.title ? String(payload.title).trim() : ''
  if (!displayName) {
    const names = activeParticipants
      .map((member) => member.displayName || member.email)
      .filter(Boolean)
    displayName = names.join(', ')
  }
  if (!displayName) {
    displayName = members.length > 1 ? 'Conversation' : 'Nouvelle conversation'
  }
  let conversationAvatar = payload.avatar_url || null
  if (!conversationAvatar && payload.type === 'direct' && activeParticipants.length === 1) {
    conversationAvatar = activeParticipants[0]?.avatarUrl || null
  }
  const normalizedConversationAvatar = normalizeAvatarUrl(conversationAvatar, { baseUrl: backendBase })
  return {
    id: String(payload.id),
    title: payload.title || null,
    topic: payload.topic || null,
    type: payload.type || 'group',
    archived: Boolean(payload.archived),
    createdAt,
    members,
    participants: activeParticipants,
    displayName,
    initials: computeInitials(displayName),
    avatarUrl: normalizedConversationAvatar,
    blockedByMe: Boolean(payload.blocked_by_viewer),
    blockedByOther: Boolean(payload.blocked_by_other),
  }
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



const selectedConversation = computed(() => {
  if (!selectedConversationId.value) return null
  return conversations.value.find((conv) => conv.id === selectedConversationId.value) || null
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

function displayNameForUser(userId) {
  if (!userId) return 'Participant'
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return 'Participant'
  const match = conv.members.find((member) => memberUserId(member) === String(userId))
  return match?.displayName || match?.email || 'Participant'
}

const conversationOwners = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return []
  return conv.members.filter((member) => member.role === 'owner')
})

const conversationOwnerSummary = computed(() => {
  if (!conversationOwners.value.length) return 'Non défini'
  return conversationOwners.value
    .map((member) => member.displayName || member.email || 'Membre')
    .join(', ')
})

const presenceByUserId = computed(() => {
  const map = new Map()
  const snapshot = presenceSnapshot.value?.users || []
  snapshot.forEach((entry) => {
    if (!entry?.userId) return
    map.set(String(entry.userId), entry)
  })
  return map
})

const presenceSummary = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return ''
  const snapshot = presenceSnapshot.value
  const snapshotUsers = snapshot?.users || []
  const snapshotTimestamp = snapshot?.timestamp instanceof Date ? snapshot.timestamp.getTime() : 0
  const isSnapshotFresh =
    snapshotUsers.length && snapshotTimestamp && Date.now() - snapshotTimestamp < PRESENCE_STALE_MS
  if (isSnapshotFresh) {
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const others = conv.members.filter((member) => memberUserId(member) !== selfId)
    if (!others.length) return ''
    if (others.length === 1) {
      const target = others[0]
      return memberPresenceText(target.userId || target.id)
    }
    const activeMembers = others.filter((member) => {
      const presence = memberPresence(member.userId || member.id)
      return presence.status === 'online' || presence.status === 'available'
    })
    if (!activeMembers.length) {
      return 'Tous les membres sont hors ligne'
    }
    if (activeMembers.length === 1) {
      return `${displayNameForUser(activeMembers[0].id)} est en ligne`
    }
    return `${activeMembers.length} membres en ligne`
  }
  if (conv.type === 'direct') {
    const manual = manualPresenceFromConversation(conv)
    if (manual) {
      return manual.label
    }
  }
  const entry = conversationPresence[conv.id]
  if (entry?.label) return entry.label
  return STATUS_LABELS.offline
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

const primaryParticipantPresence = computed(() => {
  const conv = selectedConversation.value
  if (!conv) {
    return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
  }
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  const target =
    conv.participants.find((member) => memberUserId(member) !== selfId) ||
    conv.members.find((member) => memberUserId(member) !== selfId)
  if (!target) {
    return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
  }
  return memberPresence(target.userId || target.id)
})

const typingIndicatorText = computed(() => {
  if (!typingUsers.value.length) return ''
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  const participants = typingUsers.value.filter((id) => id !== selfId)
  if (!participants.length) return ''
  const names = participants.map((id) => displayNameForUser(id)).filter(Boolean)
  if (!names.length) return ''
  if (names.length === 1) {
    return `${names[0]} est en train d'écrire...`
  }
  if (names.length === 2) {
    return `${names[0]} et ${names[1]} sont en train d'écrire...`
  }
  return `${names[0]}, ${names[1]} et ${names.length - 2} autres écrivent...`
})

const remoteDisplayName = computed(() => {
  if (callState.remoteUserId) {
    return displayNameForUser(callState.remoteUserId)
  }
  return 'Participant'
})

const callStatusLabel = computed(() => {
  switch (callState.status) {
    case 'incoming':
      return `${remoteDisplayName.value} vous appelle`
    case 'outgoing':
      return `Connexion avec ${remoteDisplayName.value}`
    case 'connecting':
      return `Initialisation de l'appel`
    case 'connected':
      return `En communication avec ${remoteDisplayName.value}`
    default:
      return 'Appel s?curis?'
  }
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
const readyAttachments = computed(() => pendingAttachments.value.filter((entry) => entry.status === 'ready'))
const hasAttachmentInProgress = computed(() => pendingAttachments.value.some((entry) => entry.status === 'uploading'))
const isEditingMessage = computed(() => composerState.mode === 'edit' && Boolean(composerState.targetMessageId))
const hasComposerContext = computed(() => {
  return (
    composerState.mode !== 'new' ||
    composerState.replyTo !== null ||
    composerState.forwardFrom !== null
  )
})

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
        forwardPickerInput.value?.focus()
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
    const list = Array.isArray(data) ? data.map((item) => normalizeConversation(item)).filter(Boolean) : []
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
    const list = Array.isArray(response.data) ? response.data.map(normalizeMessage) : []
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


function normalizeMessage(payload) {
  const convId = String(payload.conversation_id || payload.conv_id || '')
  const authorId = payload.author_id ? String(payload.author_id) : null
  const createdAt = payload.created_at ? new Date(payload.created_at) : new Date()
  const displayName =
    payload.author_display_name || (authorId && authorId === currentUserId.value ? 'Vous' : 'Participant')

  const content = (payload.content || '').toString()
  const gifLinks = detectGifLinks(content)
  const textWithoutGifs = stripGifLinks(content, gifLinks)
  const previewContent =
    gifLinks.length && !textWithoutGifs ? 'GIF partagé' : textWithoutGifs || content

  const reactions = Array.isArray(payload.reactions)

    ? payload.reactions.map((reaction) => ({

        emoji: reaction.emoji,

        count: Number(reaction.count || 0),

        reacted: Boolean(reaction.reacted),

      }))

    : []

  const deliveredAt = payload.delivered_at ? new Date(payload.delivered_at) : null
  const readAt = payload.read_at ? new Date(payload.read_at) : null
  const pinnedAt = payload.pinned_at ? new Date(payload.pinned_at) : null
  const attachments = Array.isArray(payload.attachments)
    ? payload.attachments.map((attachment) => mapAttachmentPayload(attachment)).filter(Boolean)
    : []
  const editedAt = payload.edited_at ? new Date(payload.edited_at) : null
  const deletedAt = payload.deleted_at ? new Date(payload.deleted_at) : null
  const deleted = Boolean(payload.deleted)
  const replyTo = payload.reply_to ? mapReferencePayload(payload.reply_to) : null
  const forwardFrom = payload.forward_from ? mapReferencePayload(payload.forward_from) : null
  const streamPosition = Number(payload.stream_position ?? payload.streamPosition ?? null)
  const deliverySummaryRaw = payload.delivery_summary || {}
  const deliverySummary = {
    total: Number(deliverySummaryRaw.total || 0),
    delivered: Number(deliverySummaryRaw.delivered || 0),
    read: Number(deliverySummaryRaw.read || 0),
    pending: Number(deliverySummaryRaw.pending || 0),
  }
  return {
    id: String(payload.id || payload.message_id || generateLocalId()),
    conversationId: convId,
    authorId,
    displayName,
    avatarUrl: normalizeAvatarUrl(payload.author_avatar_url || null, { baseUrl: backendBase }),
    content: deleted ? '' : content,
    createdAt,
    isSystem: Boolean(payload.is_system),
    sentByMe: Boolean(authorId && currentUserId.value && authorId === String(currentUserId.value)),
    deliveryState: payload.delivery_state || null,
    deliveredAt,
    readAt,
    reactions,
    pinned: Boolean(payload.pinned),
    pinnedAt,
    pinnedBy: payload.pinned_by ? String(payload.pinned_by) : null,
    security: {
      scheme: payload.encryption_scheme || 'confidentiel',
      metadata: payload.encryption_metadata || {},
    },
    preview: `${displayName}: ${previewContent || ''}`.trim(),
    attachments,
    editedAt,
    deletedAt,
    deleted,
    replyTo,
    forwardFrom,
    streamPosition,
    deliverySummary,
  }
}

function memberUserId(member) {
  if (!member) return null
  if (member.userId) return String(member.userId)
  if (member.user_id) return String(member.user_id)
  if (member.contact_user_id) return String(member.contact_user_id)
  return member.id ? String(member.id) : null
}

function matchesUser(member, userId) {
  if (!member || !userId) return false
  return memberUserId(member) === String(userId)
}

function mapAttachmentPayload(raw) {
  if (!raw) return null

  return {

    id: String(raw.id || raw.attachment_id || generateLocalId()),

    fileName: raw.file_name || raw.filename || raw.name || 'Pièce jointe',

    mimeType: raw.mime_type || raw.mimeType || null,

    sizeBytes: raw.size_bytes || raw.sizeBytes || null,

    sha256: raw.sha256 || null,

    downloadUrl: raw.download_url || raw.downloadUrl || null,

    encryption: raw.encryption || {},

  }

}



function mapReferencePayload(raw) {

  if (!raw) return null

  return {

    id: String(raw.id || raw.message_id || generateLocalId()),

    authorDisplayName: raw.author_display_name || 'Participant',

    excerpt: raw.excerpt || '',

    createdAt: raw.created_at ? new Date(raw.created_at) : null,

    deleted: Boolean(raw.deleted),

    attachments: Number(raw.attachments || 0),

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
  const normalized = normalizeConversation(payload)
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

function mapInvite(invite) {
  if (!invite) return null
  return {
    id: invite.id,
    email: invite.email,
    role: invite.role,
    token: invite.token,
    expiresAt: invite.expires_at ? new Date(invite.expires_at) : null,
    acceptedAt: invite.accepted_at ? new Date(invite.accepted_at) : null,
  }
}

function roleLabel(role) {
  const option = conversationRoles.find((entry) => entry.value === role)
  return option ? option.label : role
}

function memberPresence(memberId) {
  const key = memberId ? String(memberId) : null
  if (!key) {
    return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
  }
  const base = presenceByUserId.value.get(key) || { status: 'offline', lastSeen: null }
  const member = findMemberById(key)
  const manual = deriveStatusFromMessage(member?.statusMessage || '')
  const status = manual || normalizePresenceStatus(base.status)
  const label =
    manual && member?.statusMessage
      ? member.statusMessage
      : STATUS_LABELS[status] || STATUS_LABELS.offline
  return { status, label, lastSeen: base.lastSeen || null }
}

function memberPresenceText(memberId) {
  const entry = memberPresence(memberId)
  if (entry.status === 'online' || entry.status === 'available') {
    return entry.label || STATUS_LABELS.online
  }
  if (entry.label && entry.label !== STATUS_LABELS.offline) {
    return entry.label
  }
  if (entry.lastSeen instanceof Date) {
    return `${STATUS_LABELS.offline} · vu ${formatAbsolute(entry.lastSeen)}`
  }
  return STATUS_LABELS.offline
}

function findMemberById(memberId) {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return null
  const key = memberId ? String(memberId) : null
  if (!key) return null
  return (
    conv.members.find((member) => String(member.id) === key) ||
    conv.members.find((member) => memberUserId(member) === key) ||
    null
  )
}

function normalizePresenceStatus(status) {
  if (!status) return 'offline'
  const value = status.toLowerCase()
  if (value === 'online' || value === 'available') return 'online'
  if (value === 'meeting') return 'meeting'
  if (value === 'busy') return 'busy'
  if (value === 'dnd') return 'dnd'
  if (value === 'away') return 'away'
  return 'offline'
}

function deriveStatusFromMessage(message) {
  if (!message) return null
  const normalized = stripDiacritics(message).toLowerCase()
  if (normalized.includes('reunion') || normalized.includes('meeting')) return 'meeting'
  if (normalized.includes('pas deranger')) return 'dnd'
  if (normalized.includes('occup') || normalized.includes('busy')) return 'busy'
  if (normalized.includes('absent')) return 'away'
  if (normalized.includes('disponible')) return 'available'
  return null
}

function stripDiacritics(value) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

function resolveAvailabilityFromStatus(message) {
  const code = deriveStatusFromMessage(message)
  if (code && STATUS_PRESETS[code]) {
    return code
  }
  return 'available'
}

function findConversationById(conversationId) {
  const targetId = String(conversationId)
  if (selectedConversation.value && String(selectedConversation.value.id) === targetId) {
    return selectedConversation.value
  }
  return conversations.value.find((entry) => String(entry.id) === targetId) || null
}

function findMemberInConversation(conversationId, memberId) {
  const conv = findConversationById(conversationId)
  if (!conv || !Array.isArray(conv.members)) return null
  const key = memberId ? String(memberId) : null
  if (!key) return null
  return (
    conv.members.find((member) => String(member.id) === key) ||
    conv.members.find((member) => memberUserId(member) === key) ||
    null
  )
}

function manualPresenceFromConversation(conv) {
  if (!conv || conv.type !== 'direct') return null
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  const target =
    (Array.isArray(conv.participants) &&
      conv.participants.find((member) => !selfId || memberUserId(member) !== selfId)) ||
    (Array.isArray(conv.members) &&
      conv.members.find((member) => !selfId || memberUserId(member) !== selfId))
  if (!target) return null
  return { status: 'offline', label: STATUS_LABELS.offline }
}

function manualPresenceForConversationId(convId) {
  const conv = findConversationById(convId)
  if (!conv) return null
  return manualPresenceFromConversation(conv)
}

function setConversationPresence(convId, entry, source = 'manual') {
  if (!convId) return
  const key = String(convId)
  conversationPresence[key] = entry
  conversationPresenceSource[key] = source
}

function getConversationPresenceSource(convId) {
  return conversationPresenceSource[String(convId)] || 'unknown'
}

function refreshManualPresenceForConversation(convOrId) {
  const conv =
    typeof convOrId === 'object' && convOrId !== null ? convOrId : findConversationById(convOrId)
  if (!conv) return
  if (conv.type !== 'direct') {
    if (!conversationPresence[conv.id]) {
      setConversationPresence(conv.id, { status: 'offline', label: STATUS_LABELS.offline }, 'unknown')
    }
    return
  }
  if (getConversationPresenceSource(conv.id) === 'realtime') {
    return
  }
  const manual = manualPresenceFromConversation(conv)
  if (manual) {
    setConversationPresence(conv.id, manual, 'manual')
  } else if (!conversationPresence[conv.id]) {
    setConversationPresence(conv.id, { status: 'offline', label: STATUS_LABELS.offline }, 'unknown')
  }
}

function refreshManualPresenceForAll() {
  conversations.value.forEach((conv) => refreshManualPresenceForConversation(conv))
}

function summarizePresenceEntries(entries) {
  if (!entries.length) {
    return { status: 'offline', label: STATUS_LABELS.offline }
  }
  const normalized = entries.map((entry) => normalizePresenceStatus(entry.status))
  if (normalized.some((status) => status === 'meeting')) {
    return { status: 'meeting', label: STATUS_LABELS.meeting }
  }
  if (normalized.some((status) => status === 'busy' || status === 'dnd')) {
    return { status: 'busy', label: STATUS_LABELS.busy }
  }
  if (normalized.some((status) => status === 'online')) {
    return { status: 'online', label: STATUS_LABELS.online }
  }
  if (normalized.some((status) => status === 'away')) {
    return { status: 'away', label: STATUS_LABELS.away }
  }
  return { status: 'offline', label: STATUS_LABELS.offline }
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

function resetRemoteTyping() {
  Object.keys(typingTimestamps).forEach((key) => delete typingTimestamps[key])
  typingUsers.value = []
}

function cleanupRemoteTyping() {
  const now = Date.now()
  let changed = false
  for (const [key, ts] of Object.entries(typingTimestamps)) {
    if (now - ts > REMOTE_TYPING_STALE_MS) {
      delete typingTimestamps[key]
      changed = true
    }
  }
  if (changed) {
    typingUsers.value = Object.keys(typingTimestamps)
  }
}

function resetPresenceState() {
  presenceSnapshot.value = { users: [], timestamp: null }
  if (selectedConversationId.value) {
    setConversationPresence(selectedConversationId.value, { status: 'offline', label: STATUS_LABELS.offline }, 'unknown')
    refreshManualPresenceForConversation(selectedConversationId.value)
  }
  resetRemoteTyping()
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
  const attachmentsPayload = readyAttachments.value
    .map((entry) => entry.descriptor?.upload_token)
    .filter(Boolean)
    .map((token) => ({ upload_token: token }))
  const draftContent = messageInput.value.trim()
  const replyToId =
    composerState.replyTo && isValidUuid(composerState.replyTo.id) ? composerState.replyTo.id : null
  const forwardId =
    composerState.forwardFrom && isValidUuid(composerState.forwardFrom.id)
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
    attachments: mapOptimisticAttachments(readyAttachments.value),
    replyTo: cloneComposerReference(composerState.replyTo),
    forwardFrom: cloneComposerReference(composerState.forwardFrom),
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
    const message = normalizeMessage(data)
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
    const message = normalizeMessage(data)
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
  const message = normalizeMessage(payload)
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

function handleRealtimeTyping(evt) {
  const eventName = evt?.event
  const userIdRaw = evt?.payload?.user_id
  const convId = evt?.payload?.conversation_id || evt?.conversation_id
  if (!selectedConversationId.value || !convId || String(convId) !== String(selectedConversationId.value)) {
    return
  }
  if (!eventName || !userIdRaw) return
  const userId = String(userIdRaw)
  if (currentUserId.value && String(currentUserId.value) === userId) return
  if (eventName === 'typing:start') {
    typingTimestamps[userId] = Date.now()
  } else if (eventName === 'typing:stop') {
    delete typingTimestamps[userId]
  }
  typingUsers.value = Object.keys(typingTimestamps)
}

function applyPresencePayload(payload) {
  if (!payload) return
  const incomingConvId = payload.conversation_id ? String(payload.conversation_id) : null
  const currentConvId = selectedConversationId.value ? String(selectedConversationId.value) : null
  const isCurrentConversation = !incomingConvId || incomingConvId === currentConvId
  const convId = incomingConvId || currentConvId
  const selfId = currentUserId.value ? String(currentUserId.value) : null

  const rawUsers = Array.isArray(payload.users) ? payload.users : []
  const users = rawUsers
        .map((entry) => {
          const userId = entry?.user_id ? String(entry.user_id) : entry?.id ? String(entry.id) : ''
          if (!userId) return null
          if (selfId && userId === selfId) return null
          const baseStatus = normalizePresenceStatus(entry?.status || 'offline')
          const member = convId ? findMemberInConversation(convId, userId) : findMemberById(userId)
          const manualStatus = member?.statusMessage ? deriveStatusFromMessage(member.statusMessage) : null
          const status = manualStatus || baseStatus
          const label =
            manualStatus && member?.statusMessage
              ? member.statusMessage
              : STATUS_LABELS[status] || STATUS_LABELS.offline
          return {
            userId,
            status,
            label,
            lastSeen: entry?.last_seen ? new Date(entry.last_seen) : null,
          }
        })
        .filter(Boolean)
  if (isCurrentConversation) {
    presenceSnapshot.value = {
      users,
      timestamp: payload.timestamp ? new Date(payload.timestamp) : new Date(),
    }
  }
  if (convId) {
    let entry
    let source = 'realtime'
    if (users.length) {
      entry = summarizePresenceEntries(users)
    } else if (rawUsers.length) {
      entry = { status: 'offline', label: STATUS_LABELS.offline }
    } else {
      const manual = manualPresenceForConversationId(convId)
      if (manual) {
        entry = manual
        source = 'manual'
      } else {
        entry = { status: 'offline', label: STATUS_LABELS.offline }
        source = 'unknown'
      }
    }
    setConversationPresence(convId, entry, source)
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

async function loadAvailabilityStatus() {
  try {
    const { data } = await api.get('/me/profile')
    const statusMessage = data?.status_message || ''
    const code = resolveAvailabilityFromStatus(statusMessage)
    persistStatusMessage(statusMessage, code)
    myAvailability.value = code
    applyLocalStatusMessage(statusMessage)
  } catch {
    myAvailability.value = 'available'
  }
}

async function onAvailabilityChange(value) {
  if (value === myAvailability.value) return
  const next = STATUS_PRESETS[value] ? value : 'available'
  const previous = myAvailability.value
  myAvailability.value = next
  const message = STATUS_PRESETS[next].message || ''
  try {
    await api.put('/me/profile', { status_message: message || null })
    persistStatusMessage(message, next)
    applyLocalStatusMessage(message)
    broadcastProfileUpdate({ status_message: message || null, status_code: next })
  } catch (err) {
    console.error('Impossible de mettre ? jour le statut', err)
    myAvailability.value = previous
  }
}
function persistStatusMessage(value, codeHint) {
  const message = value || ''
  const code = codeHint || resolveAvailabilityFromStatus(message)
  try {
    if (message) {
      localStorage.setItem('status_message', message)
    } else {
      localStorage.removeItem('status_message')
    }
    if (code) {
      localStorage.setItem('status_code', code)
    } else {
      localStorage.removeItem('status_code')
    }
  } catch {}
}

function applyLocalStatusMessage(message) {
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  if (!selfId) return
  conversations.value.forEach((conv) => {
    if (!Array.isArray(conv.members)) return
    conv.members.forEach((member) => {
      if (memberUserId(member) === selfId) {
        member.statusMessage = message || ''
      }
    })
  })
  if (selectedConversation.value && Array.isArray(selectedConversation.value.members)) {
    selectedConversation.value.members.forEach((member) => {
      if (memberUserId(member) === selfId) {
        member.statusMessage = message || ''
      }
    })
  }
  refreshManualPresenceForAll()
}
function handleProfileBroadcast(event) {
  const detail = event?.detail || {}
  if (Object.prototype.hasOwnProperty.call(detail, 'status_message')) {
    const statusMessage = detail.status_message || ''
    const code = resolveAvailabilityFromStatus(statusMessage)
    persistStatusMessage(statusMessage, code)
    myAvailability.value = code
    applyLocalStatusMessage(statusMessage)
  }
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

function initiateForward(message) {
  if (!message) return
  closeTransientMenus()
  forwardPicker.open = true
  forwardPicker.message = message
  forwardPicker.query = ''
}

function cancelForwardSelection() {
  forwardPicker.open = false
  forwardPicker.message = null
  forwardPicker.query = ''
}

async function confirmForwardTarget(conversationId) {
  if (!forwardPicker.message) {
    cancelForwardSelection()
    return
  }
  const targetMessage = forwardPicker.message
  cancelForwardSelection()
  const normalizedId = conversationId ? String(conversationId) : null
  if (normalizedId && normalizedId !== selectedConversationId.value) {
    try {
      await selectConversation(normalizedId)
    } catch (error) {
      console.warn('Impossible d’ouvrir la conversation cible pour le transfert.', error)
    }
  }
  startForward(targetMessage)
}

function startReply(message) {
  if (!message) return
  composerState.mode = 'reply'
  composerState.replyTo = message
  composerState.forwardFrom = null
  composerState.targetMessageId = null
}

function startForward(message) {
  if (!message) return
  composerState.mode = 'forward'
  composerState.forwardFrom = message
  composerState.replyTo = null
  composerState.targetMessageId = null
  if (!messageInput.value) {
    messageInput.value = message.content || ''
  }
}

function startEdit(message) {
  if (!message) return
  composerState.mode = 'edit'
  composerState.targetMessageId = message.id
  composerState.replyTo = null
  composerState.forwardFrom = null
  messageInput.value = message.content || ''
  clearPendingAttachments()
}

function cancelComposerContext() {
  resetComposerState()
}

function triggerAttachmentPicker() {
  attachmentError.value = ''
  if (!selectedConversationId.value) {
    attachmentError.value = 'Sélectionnez une conversation avant d\'ajouter un fichier.'
    return
  }
  if (attachmentInput.value) {
    attachmentInput.value.value = ''
    attachmentInput.value.click()
  }
}
function onAttachmentChange(event) {
  const files = Array.from(event.target?.files || [])
  if (!files.length) return
  files.forEach((file) => queueAttachment(file))
}

function queueAttachment(file) {
  if (!file) return
  const entry = reactive({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: file.name,
    size: file.size,
    type: file.type,
    file,
    status: 'uploading',
    progress: 0,
    descriptor: null,
    error: '',
  })
  pendingAttachments.value = [...pendingAttachments.value, entry]
  uploadAttachmentFile(entry)
}

async function uploadAttachmentFile(entry) {
  if (!selectedConversationId.value) {
    entry.status = 'error'
    entry.error = 'Aucune conversation active.'
    return
  }
  attachmentError.value = ''
  try {
    const descriptor = await uploadAttachment(selectedConversationId.value, entry.file, {
      onUploadProgress: (event) => {
        if (!event || !event.total) return
        entry.progress = Math.min(100, Math.round((event.loaded / event.total) * 100))
      },
    })
    entry.descriptor = descriptor
    entry.status = 'ready'
    entry.progress = 100
  } catch (err) {
    entry.status = 'error'
    entry.error = extractError(err, 'Impossible de téléverser le fichier.')
    attachmentError.value = entry.error
  }
}

function removeAttachment(entryId) {
  pendingAttachments.value = pendingAttachments.value.filter((item) => item.id !== entryId)
}

function clearPendingAttachments() {
  pendingAttachments.value = []
  attachmentError.value = ''
}

function confirmDeleteMessage(message) {
  if (!message || !selectedConversationId.value) return
  deleteDialog.message = message
  deleteDialog.error = ''
  deleteDialog.visible = true
}

function closeDeleteDialog() {
  if (deleteDialog.loading) return
  deleteDialog.visible = false
  deleteDialog.message = null
  deleteDialog.error = ''
}

async function performDeleteMessage() {
  if (!deleteDialog.message || !selectedConversationId.value) return
  deleteDialog.loading = true
  deleteDialog.error = ''
  try {
    const data = await deleteConversationMessage(selectedConversationId.value, deleteDialog.message.id)
    applyMessageUpdate(normalizeMessage(data))
    closeDeleteDialog()
  } catch (err) {
    deleteDialog.error = extractError(err, "Impossible de supprimer le message.")
  } finally {
    deleteDialog.loading = false
  }
}

function syncConversationFormFromSelected() {
  const conv = selectedConversation.value
  if (!conv) return
  conversationForm.title = conv.title || ''
  conversationForm.topic = conv.topic || ''
  conversationForm.archived = Boolean(conv.archived)
}

function clearConversationNotice() {
  if (conversationNoticeTimer) {
    clearTimeout(conversationNoticeTimer)
    conversationNoticeTimer = null
  }
  conversationInfoNotice.value = ''
}

function setConversationNotice(message) {
  clearConversationNotice()
  if (message) {
    conversationInfoNotice.value = message
    conversationNoticeTimer = setTimeout(() => {
      conversationInfoNotice.value = ''
      conversationNoticeTimer = null
    }, 5000)
  }
}

async function openConversationPanel() {
  if (!selectedConversation.value) return
  conversationInfoError.value = ''
  clearConversationNotice()
  syncConversationFormFromSelected()
  showConversationPanel.value = true
  if (canManageConversation.value && selectedConversationId.value) {
    await loadConversationInvites(selectedConversationId.value)
  }
}

function closeConversationPanel() {
  showConversationPanel.value = false
  invites.value = []
  clearConversationNotice()
}

async function saveConversationSettings() {
  if (!selectedConversationId.value) return
  savingConversation.value = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    const payload = {
      title: conversationForm.title.trim() || null,
      topic: conversationForm.topic.trim() || null,
      archived: conversationForm.archived,
    }
    const data = await updateConversation(selectedConversationId.value, payload)
    applyConversationPatch(data)
    setConversationNotice('Conversation mise à jour.')
  } catch (err) {
    conversationInfoError.value = extractError(err, "Impossible d'enregistrer la conversation.")
  } finally {
    savingConversation.value = false
  }
}

async function leaveCurrentConversation() {
  if (!selectedConversationId.value) return
  leavingConversation.value = true
  conversationInfoError.value = ''
  clearConversationNotice()
  const convId = selectedConversationId.value
  try {
    await leaveConversation(convId)
    conversations.value = conversations.value.filter((conv) => conv.id !== convId)
    delete conversationMeta[convId]
    showConversationPanel.value = false
    messages.value = []
    disconnectRealtime()
    selectedConversationId.value = null
    const fallback = conversations.value[0]
    if (fallback) {
      selectConversation(fallback.id)
    }
  } catch (err) {
    conversationInfoError.value = extractError(err, 'Impossible de quitter la conversation.')
  } finally {
    leavingConversation.value = false
  }
}

async function loadConversationInvites(convId) {
  if (!canManageConversation.value || !convId) {
    invites.value = []
    return
  }
  loadingInvites.value = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    const data = await listConversationInvites(convId)
    invites.value = Array.isArray(data) ? data.map((invite) => mapInvite(invite)).filter(Boolean) : []
  } catch (err) {
    conversationInfoError.value = extractError(err, 'Impossible de charger les invitations.')
  } finally {
    loadingInvites.value = false
  }
}

async function submitInvite() {
  if (!selectedConversationId.value || !inviteForm.email.trim()) return
  inviteBusy.value = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    const payload = {
      email: inviteForm.email.trim(),
      role: inviteForm.role,
      expires_in_hours: inviteForm.expiresInHours,
    }
    const data = await createConversationInvite(selectedConversationId.value, payload)
    const mapped = mapInvite(data)
    if (mapped) {
      invites.value = [mapped, ...invites.value]
    }
    inviteForm.email = ''
    setConversationNotice('Invitation créée et envoyée.')
  } catch (err) {
    conversationInfoError.value = extractError(err, "Impossible de créer l'invitation.")
  } finally {
    inviteBusy.value = false
  }
}

async function revokeInvite(inviteId) {
  if (!selectedConversationId.value || !inviteId) return
  inviteRevokeBusy[inviteId] = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    await revokeConversationInvite(selectedConversationId.value, inviteId)
    invites.value = invites.value.filter((invite) => invite.id !== inviteId)
    setConversationNotice('Invitation révoquée.')
  } catch (err) {
    conversationInfoError.value = extractError(err, "Impossible de révoquer l'invitation.")
  } finally {
    delete inviteRevokeBusy[inviteId]
  }
}

function formatInviteStatus(invite) {
  if (!invite) return ''
  if (invite.acceptedAt) {
    return `Acceptée ${formatAbsolute(invite.acceptedAt)}`
  }
  if (invite.expiresAt) {
    return `Expire ${formatAbsolute(invite.expiresAt)}`
  }
  return ''
}

async function updateMemberRole(member, role) {
  if (!selectedConversationId.value || !member?.id || !role || member.role === role) return
  memberBusy[member.id] = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { role })
    applyMemberPayload(data)
    setConversationNotice('Rôle du membre mis à jour.')
  } catch (err) {
    conversationInfoError.value = extractError(err, "Impossible de mettre à jour le membre.")
  } finally {
    delete memberBusy[member.id]
  }
}

async function muteMember(member, minutes = 60) {
  if (!selectedConversationId.value || !member?.id) return
  memberBusy[member.id] = true
  conversationInfoError.value = ''
  clearConversationNotice()
  const mutedUntil = new Date(Date.now() + minutes * 60000).toISOString()
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: mutedUntil })
    applyMemberPayload(data)
    setConversationNotice(`Membre mis en sourdine pendant ${minutes} min.`)
  } catch (err) {
    conversationInfoError.value = extractError(err, "Impossible de mettre le membre en sourdine.")
  } finally {
    delete memberBusy[member.id]
  }
}

async function unmuteMember(member) {
  if (!selectedConversationId.value || !member?.id) return
  memberBusy[member.id] = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: null })
    applyMemberPayload(data)
    setConversationNotice('Sourdine désactivée pour ce membre.')
  } catch (err) {
    conversationInfoError.value = extractError(err, "Impossible de rétablir le membre.")
  } finally {
    delete memberBusy[member.id]
  }
}

async function removeMember(member) {
  if (!selectedConversationId.value || !member?.id) return
  memberBusy[member.id] = true
  conversationInfoError.value = ''
  clearConversationNotice()
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { state: 'left' })
    applyMemberPayload(data)
    setConversationNotice('Membre retiré de la conversation.')
  } catch (err) {
    conversationInfoError.value = extractError(err, 'Impossible de retirer le membre.')
  } finally {
    delete memberBusy[member.id]
  }
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

function getDefaultCallTarget() {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return null
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  return (
    conv.members.find(
      (member) => member.state === 'active' && (!selfId || memberUserId(member) !== selfId),
    ) || null
  )
}

function setCallError(err) {
  if (!err) {
    callState.error = ''
    return
  }
  if (typeof err === 'string') {
    callState.error = err
  } else {
    callState.error = err.message || "La connexion ? l'appel a ?chou?."
  }
}

function sendCallSignal(event, payload = {}) {
  if (!socketRef.value || !selectedConversationId.value) return
  try {
    socketRef.value.send({
      event,
      payload: {
        conversation_id: selectedConversationId.value,
        ...payload,
      },
    })
  } catch {}
}

function stopStream(stream) {
  if (!stream) return
  stream.getTracks().forEach((track) => {
    try {
      track.stop()
    } catch {}
  })
}

async function requestMedia(kind = 'audio') {
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
    throw new Error('Votre navigateur ne permet pas les appels s?curis?s.')
  }
  const constraints = {
    audio: true,
    video: kind === 'video',
  }
  return navigator.mediaDevices.getUserMedia(constraints)
}

async function createPeerConnection(stream) {
  if (peerConnection) {
    try {
      peerConnection.close()
    } catch {}
    peerConnection = null
  }
  peerConnection = new RTCPeerConnection(rtcConfig)
  peerConnection.ontrack = (event) => {
    const [remote] = event.streams
    if (remote) {
      callState.remoteStream = remote
    }
  }
  peerConnection.onicecandidate = (event) => {
    if (event.candidate && callState.callId && callState.remoteUserId) {
      sendCallSignal('call:candidate', {
        call_id: callState.callId,
        target_user_id: callState.remoteUserId,
        candidate: {
          candidate: event.candidate.candidate,
          sdpMid: event.candidate.sdpMid,
          sdpMLineIndex: event.candidate.sdpMLineIndex,
        },
      })
    }
  }
  peerConnection.onconnectionstatechange = () => {
    if (!peerConnection) return
    if (peerConnection.connectionState === 'connected') {
      callState.status = 'connected'
    } else if (peerConnection.connectionState === 'failed') {
      setCallError('La connexion a ?chou?.')
      endCall(true)
    }
  }
  if (stream) {
    stream.getTracks().forEach((track) => {
      peerConnection.addTrack(track, stream)
    })
  }
}

function serializeDescription(desc) {
  if (!desc) return null
  return { type: desc.type, sdp: desc.sdp }
}

async function startCall(kind = 'audio') {
  callState.error = ''
  if (!selectedConversationId.value) {
    setCallError('Aucune conversation active.')
    return
  }
  if (!socketRef.value) {
    setCallError('Canal temps r?el indisponible.')
    return
  }
  if (callState.status !== 'idle') {
    setCallError('Un autre appel est d?j? en cours.')
    return
  }
  const target = getDefaultCallTarget()
  if (!target) {
    setCallError('Aucun interlocuteur disponible dans cette conversation.')
    return
  }
  callState.kind = kind
  callState.remoteUserId = target.id
  callState.callId = generateCallId()
  callState.initiator = true
  callState.status = 'connecting'
  callState.error = ''
  callControls.micEnabled = true
  callControls.cameraEnabled = kind === 'video'
  try {
    const stream = await requestMedia(kind)
    callState.localStream = stream
    await createPeerConnection(stream)
    const offer = await peerConnection.createOffer()
    await peerConnection.setLocalDescription(offer)
    callState.status = 'outgoing'
    const description = serializeDescription(peerConnection.localDescription)
    if (!description) throw new Error('Impossible de pr\u00E9parer l\'offre.')
    sendCallSignal('call:offer', {
      call_id: callState.callId,
      target_user_id: callState.remoteUserId,
      kind,
      sdp: description,
    })
  } catch (err) {
    setCallError(err)
    endCall(true)
  }
}

function cancelOutgoingCall() {
  endCall(false, { reason: 'canceled' })
}

function hangupCall() {
  endCall(false, { reason: 'hangup' })
}

function rejectIncomingCall() {
  endCall(false, { reason: 'decline' })
}

async function acceptIncomingCall() {
  const offer = callState.incomingOffer
  if (!offer) return
  callState.error = ''
  callState.status = 'connecting'
  callControls.micEnabled = true
  callControls.cameraEnabled = callState.kind === 'video'
  try {
    const stream = await requestMedia(callState.kind)
    callState.localStream = stream
    await createPeerConnection(stream)
    if (offer.sdp) {
      await peerConnection.setRemoteDescription(offer.sdp)
    }
    const answer = await peerConnection.createAnswer()
    await peerConnection.setLocalDescription(answer)
    flushPendingCandidates()
    const description = serializeDescription(peerConnection.localDescription)
    if (!description) throw new Error('Impossible de pr\u00E9parer la r\u00E9ponse.')
    sendCallSignal('call:answer', {
      call_id: callState.callId,
      target_user_id: callState.remoteUserId,
      sdp: description,
    })
    callState.incomingOffer = null
  } catch (err) {
    setCallError(err)
    endCall(true)
  }
}

function endCall(silent = false, options = {}) {
  const currentCallId = callState.callId
  const remoteId = callState.remoteUserId
  if (peerConnection) {
    try {
      peerConnection.ontrack = null
      peerConnection.onicecandidate = null
      peerConnection.close()
    } catch {}
    peerConnection = null
  }
  stopStream(callState.localStream)
  stopStream(callState.remoteStream)
  callState.localStream = null
  callState.remoteStream = null
  callState.incomingOffer = null
  callState.status = 'idle'
  callState.kind = 'audio'
  callState.callId = null
  callState.remoteUserId = null
  callState.initiator = false
  callState.error = ''
  callControls.micEnabled = true
  callControls.cameraEnabled = true
  pendingIceCandidates.length = 0
  if (!silent && currentCallId && remoteId) {
    sendCallSignal('call:hangup', {
      call_id: currentCallId,
      target_user_id: remoteId,
      reason: options.reason || 'hangup',
    })
  }
}

function handleCallSignal(evt) {
  const data = evt?.payload || {}
  const convId = data.conversation_id || evt.conversation_id
  if (!selectedConversationId.value || String(convId) !== String(selectedConversationId.value)) return
  const targetId = data.target_user_id ? String(data.target_user_id) : null
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  if (targetId && selfId && targetId !== selfId) return
  switch (evt.event) {
    case 'call:offer':
      handleIncomingOffer(data)
      break
    case 'call:answer':
      handleIncomingAnswer(data)
      break
    case 'call:candidate':
      handleIncomingCandidate(data)
      break
    case 'call:hangup':
      handleIncomingHangup(data)
      break
    default:
      break
  }
}

function handleIncomingOffer(data) {
  const fromUserId = data.from_user_id ? String(data.from_user_id) : null
  if (callState.status !== 'idle') {
    if (data.call_id && fromUserId) {
      sendCallSignal('call:hangup', {
        call_id: data.call_id,
        target_user_id: fromUserId,
        reason: 'busy',
      })
    }
    return
  }
  callState.callId = data.call_id || generateCallId()
  callState.kind = data.kind || 'audio'
  callState.remoteUserId = fromUserId
  callState.incomingOffer = data
  callState.status = 'incoming'
  callState.error = ''
  callControls.micEnabled = true
  callControls.cameraEnabled = callState.kind === 'video'
}

function handleIncomingAnswer(data) {
  if (!callState.callId || callState.callId !== data.call_id || !peerConnection) return
  if (data.from_user_id && !callState.remoteUserId) {
    callState.remoteUserId = String(data.from_user_id)
  }
  const answer = data.sdp
  if (answer) {
    peerConnection.setRemoteDescription(answer).then(() => {
      flushPendingCandidates()
    }).catch(() => {})
  }
}

function handleIncomingCandidate(data) {
  if (!callState.callId || callState.callId !== data.call_id) return
  const candidate = data.candidate
  if (!candidate) return
  if (!peerConnection) {
    pendingIceCandidates.push(candidate)
    return
  }
  try {
    peerConnection.addIceCandidate(candidate)
  } catch {
    pendingIceCandidates.push(candidate)
  }
}

function handleIncomingHangup(data) {
  if (!callState.callId || data.call_id !== callState.callId) return
  endCall(true)
}

function toggleMicrophone() {
  callControls.micEnabled = !callControls.micEnabled
  if (callState.localStream) {
    callState.localStream.getAudioTracks().forEach((track) => {
      track.enabled = callControls.micEnabled
    })
  }
}

function toggleCamera() {
  if (callState.kind !== 'video') return
  callControls.cameraEnabled = !callControls.cameraEnabled
  if (callState.localStream) {
    callState.localStream.getVideoTracks().forEach((track) => {
      track.enabled = callControls.cameraEnabled
    })
  }
}

function handleRealtimeCallEvent(payload) {
  handleCallSignal(payload)
}

function attachStream(el, stream) {
  if (!el) return
  if ('srcObject' in el) {
    el.srcObject = stream || null
  } else if (stream) {
    el.src = URL.createObjectURL(stream)
  } else {
    el.removeAttribute('src')
  }
}

function flushPendingCandidates() {
  if (!peerConnection || !pendingIceCandidates.length) return
  while (pendingIceCandidates.length) {
    const candidate = pendingIceCandidates.shift()
    if (!candidate) continue
    try {
      peerConnection.addIceCandidate(candidate)
    } catch {}
  }
}

watch(
  () => callState.localStream,
  (stream) => {
    attachStream(localVideoRef.value, stream || null)
  },
)

watch(
  () => callState.remoteStream,
  (stream) => {
    attachStream(remoteVideoRef.value, stream || null)
  },
)

watch(localVideoRef, (el) => attachStream(el, callState.localStream || null))
watch(remoteVideoRef, (el) => attachStream(el, callState.remoteStream || null))


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



function generateLocalId() {

  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {

    return globalThis.crypto.randomUUID()

  }

  return `msg_${Math.random().toString(36).slice(2, 10)}`

}



function queueToastNotification({ title, body, conversationId, messageId, targetRoute }) {
  const toast = {
    id: generateLocalId(),
    title: title || 'Nouveau message',
    body: body || '',
    conversationId,
    messageId,
    targetRoute: targetRoute || null,
    createdAt: new Date(),
  }
  messageToasts.value = [toast, ...messageToasts.value].slice(0, 4)
  if (toastTimers.has(toast.id)) {
    clearTimeout(toastTimers.get(toast.id))
  }
  toastTimers.set(
    toast.id,
    setTimeout(() => {
      dismissToast(toast.id)
    }, 7000),
  )
}



function dismissToast(id) {
  messageToasts.value = messageToasts.value.filter((toast) => toast.id !== id)
  if (toastTimers.has(id)) {
    clearTimeout(toastTimers.get(id))
    toastTimers.delete(id)
  }
}



async function openToastConversation(toast) {
  if (toast?.targetRoute) {
    router.push(toast.targetRoute).catch(() => {})
    dismissToast(toast.id)
    return
  }
  if (!toast?.conversationId) return
  await selectConversation(toast.conversationId)
  dismissToast(toast.id)
  await nextTick()
  if (toast.messageId) {
    await ensureMessageVisible(toast.messageId)
  }
}



function notifyNewIncomingMessage(message) {
  if (!message || message.sentByMe || message.deleted || message.isSystem) return
  const preview =
    message.preview ||
    (message.content ? String(message.content).slice(0, 140) : 'Nouveau message securise.')
  const shouldToast = message.conversationId !== selectedConversationId.value
  const browserAllowed =
    browserNotificationsEnabled.value &&
    typeof Notification !== 'undefined' &&
    Notification.permission === 'granted'
  const docHidden =
    typeof document !== 'undefined' && (document.hidden || !document.hasFocus())
  if (shouldToast) {
    queueToastNotification({
      title: message.displayName || 'Nouveau message',
      body: preview,
      conversationId: message.conversationId,
      messageId: message.id,
    })
  }
  const shouldBrowser = browserAllowed && (docHidden || shouldToast)
  if (shouldBrowser) {
    triggerBrowserNotification(message, preview)
  }
}

function triggerBrowserNotification(message, body) {
  if (typeof window !== 'undefined' && window.__covaGlobalBrowserNotifications) return
  if (!browserNotificationsEnabled.value || typeof Notification === 'undefined') return
  if (Notification.permission === 'granted') {
    const notification = new Notification(message.displayName || 'Messagerie securisee', {
      body,
      tag: message.conversationId,
    })
    notification.onclick = () => {
      window.focus()
      openToastConversation({ conversationId: message.conversationId, id: message.id, messageId: message.id })
      notification.close()
    }
    return
  }
  if (Notification.permission === 'default' && !notificationPermissionRequestPending) {
    notificationPermissionRequestPending = true
    Notification.requestPermission()
      .catch(() => {})
      .finally(() => {
        notificationPermissionRequestPending = false
      })
  }
}

function triggerBrowserNotificationFromEvent(meta) {
  if (typeof window !== 'undefined' && window.__covaGlobalBrowserNotifications) return
  if (!browserNotificationsEnabled.value || typeof Notification === 'undefined') return
  if (Notification.permission !== 'granted') return
  const notification = new Notification(meta.title || 'Messagerie securisee', {
    body: meta.body || '',
    tag: meta.conversationId || meta.type || 'notification',
  })
  notification.onclick = () => {
    window.focus()
    openToastConversation({
      id: meta.messageId || generateLocalId(),
      conversationId: meta.conversationId,
      messageId: meta.messageId,
      targetRoute: meta.targetRoute,
    })
    notification.close()
  }
}

function handleIncomingNotificationPayload(payload, origin = 'stream') {
  if (!payload || typeof payload !== 'object') return
  switch (payload.type) {
    case 'message.received':
      handleMessageNotificationEvent(payload)
      break
    case 'contact.request':
    case 'contact.accepted':
      handleContactNotificationEvent(payload)
      break
    case 'contact.blocked':
    case 'contact.unblocked':
      handleContactBlockEvent(payload)
      break
    default:
      break
  }
}

function handleMessageNotificationEvent(event) {
  if (event?.author_id && currentUserId.value && String(event.author_id) === String(currentUserId.value)) {
    return
  }
  const conversationId = event.conversation_id ? String(event.conversation_id) : null
  if (!conversationId || conversationId === String(selectedConversationId.value)) return
  const meta = ensureMeta(conversationId)
  if (event.preview) meta.lastPreview = event.preview
  meta.lastActivity = event.created_at ? new Date(event.created_at) : new Date()
  meta.unreadCount = (meta.unreadCount || 0) + 1
  setUnreadForConversation(conversationId, meta.unreadCount)
  const title = event.sender || 'Nouveau message'
  const body = event.preview || 'Message sécurisé'
  queueToastNotification({
    title,
    body,
    conversationId,
    messageId: event.message_id,
  })
  triggerBrowserNotificationFromEvent({
    title,
    body,
    conversationId,
    messageId: event.message_id,
  })
}

function notifyPendingContactsRefresh() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('cova:contacts-pending', { detail: { refresh: true } }))
}

function handleContactNotificationEvent(event) {
  const title = event.title || 'Notification de contact'
  const body = event.body || 'Une mise à jour de vos contacts est disponible.'
  queueToastNotification({
    title,
    body,
    targetRoute: '/dashboard/contacts',
  })
  triggerBrowserNotificationFromEvent({
    title,
    body,
    targetRoute: '/dashboard/contacts',
  })
  notifyPendingContactsRefresh()
}

function handleContactBlockEvent(event) {
  const isUnblocked = event.type === 'contact.unblocked'
  const flagValue = !isUnblocked
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  let otherId = null
  const updates = {}
  if (event.blocked_by || event.unblocked_by) {
    const candidate = String(event.blocked_by || event.unblocked_by)
    if (!selfId || candidate !== selfId) {
      otherId = candidate
      updates.blockedByOther = flagValue
    }
  }
  if (event.blocked_target || event.unblocked_target) {
    const candidate = String(event.blocked_target || event.unblocked_target)
    otherId = candidate
    updates.blockedByMe = flagValue
  }
  if (otherId) {
    updateConversationBlockStateByUser(otherId, updates)
  }
  const title = event.title || (isUnblocked ? 'Contact débloqué' : 'Contact bloqué')
  const body =
    event.body ||
    (isUnblocked
      ? 'La conversation a été réactivée.'
      : "La conversation est bloquée jusqu’à nouvel ordre.")
  queueToastNotification({
    title,
    body,
    targetRoute: '/dashboard/contacts',
  })
  triggerBrowserNotificationFromEvent({
    title,
    body,
    targetRoute: '/dashboard/contacts',
  })
  notifyPendingContactsRefresh()
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

    applyMessageUpdate(normalizeMessage(data))

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

    applyMessageUpdate(normalizeMessage(data))

  } catch (err) {

    console.warn('Impossible de mettre à jour la réaction', err)

  } finally {

    reactionBusy[key] = false

  }

}



function formatTime(date) {

  if (!(date instanceof Date)) return ''

  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

}



function formatListTime(date) {

  if (!(date instanceof Date)) date = new Date(date || Date.now())

  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

}



function formatAbsolute(date) {
  if (!(date instanceof Date)) return ''
  return date.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
}

function formatFileSize(bytes) {
  if (typeof bytes !== 'number' || Number.isNaN(bytes)) return ''
  if (bytes < 1024) return `${bytes} o`
  const units = ['Ko', 'Mo', 'Go', 'To']
  let size = bytes / 1024
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unit]}`
}

function downloadAttachment(attachment) {
  if (!attachment || !attachment.downloadUrl) return
  window.open(attachment.downloadUrl, '_blank', 'noopener')
}

function messagePreviewText(message) {

  if (!message) return ''

  if (message.excerpt) return message.excerpt

  if (message.content) {
    const gifs = detectGifLinks(message.content)
    const trimmed = stripGifLinks(message.content, gifs).trim()
    if (gifs.length && !trimmed) {
      return 'GIF partagé'
    }
    return trimmed || String(message.content).slice(0, 120)
  }

  if (Array.isArray(message.attachments) && message.attachments.length) {

    return `${message.attachments.length} piece(s) jointe(s)`

  }

  if (typeof message.attachments === 'number' && message.attachments > 0) {

    return `${message.attachments} piece(s) jointe(s)`

  }

  return ''

}



function extractDeliverySummary(message) {
  const summary = message.deliverySummary || {}
  return {
    total: Number(summary.total || 0),
    delivered: Number(summary.delivered || 0),
    read: Number(summary.read || 0),
    pending: Number(summary.pending || 0),
  }
}

function messageStatusLabel(message) {
  if (message.sentByMe) {
    const summary = extractDeliverySummary(message)
    if (summary.total <= 0) {
      return 'Envoy\u00e9'
    }
    if (summary.read >= summary.total) {
      return 'Lu'
    }
    if (summary.delivered > 0) {
      return 'Distribu\u00e9'
    }
    return 'Envoy\u00e9'
  }
  switch (message.deliveryState) {
    case 'read':
      return 'Lu'
    case 'delivered':
      return 'Distribu\u00e9'
    case 'queued':
      return 'Envoi'
    default:
      return ''
  }
}

function messageStatusClass(message) {
  if (message.sentByMe) {
    const summary = extractDeliverySummary(message)
    if (summary.total > 0 && summary.read >= summary.total) {
      return 'state-read'
    }
    if (summary.delivered > 0) {
      return 'state-delivered'
    }
    return 'state-queued'
  }
  switch (message.deliveryState) {
    case 'read':
      return 'state-read'
    case 'delivered':
      return 'state-delivered'
    case 'queued':
      return 'state-queued'
    default:
      return ''
  }
}

function messageStatusDetail(message) {
  if (message.deleted) return 'Supprim\u00e9'
  if (message.sentByMe) {
    const summary = extractDeliverySummary(message)
    if (!summary.total) {
      return 'Envoy\u00e9'
    }
    if (summary.read >= summary.total) {
      return `Lu par ${summary.read}/${summary.total}`
    }
    if (summary.delivered > 0) {
      return `Distribu\u00e9 \u00e0 ${summary.delivered}/${summary.total}`
    }
    return `En attente (${summary.total})`
  }
  if (message.readAt) {
    return `Lu ${formatTime(message.readAt)}`
  }
  if (message.deliveredAt) {
    return `Distribu\u00e9 ${formatTime(message.deliveredAt)}`
  }
  return ''
}

function messageSecurityLabel(message) {
  const scheme = message.security?.scheme || 'confidentiel'
  if (scheme === 'plaintext') return 'Chiffrage applicatif'
  return `Sch\u00e9ma ${scheme}`
}

function messageSecurityTooltip(message) {
  const metadata = message.security?.metadata || {}
  const lines = Object.entries(metadata).map(([key, value]) => `${key}: ${value}`)
  return [`Sch\u00e9ma: ${message.security?.scheme || 'n/a'}`, ...lines].join('\n')
}

const messageFormatters = {
  formatTime,
  formatAbsolute,
  formatFileSize,
  messageStatusLabel,
  messageStatusClass,
  messageStatusDetail,
  messageSecurityLabel,
  messageSecurityTooltip,
}




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

function makeNotificationFingerprint(payload) {
  if (!payload || typeof payload !== 'object') return `generic:${Date.now()}`
  const parts = [
    payload.type || 'generic',
    payload.message_id ||
      payload.id ||
      payload.notification_id ||
      payload.conversation_id ||
      payload.preview ||
      payload.title ||
      payload.sender ||
      payload.timestamp ||
      payload.created_at ||
      JSON.stringify(payload).slice(0, 60),
  ]
  return parts.join(':')
}

function processNotificationPayload(payload, origin = 'stream') {
  if (!payload || typeof payload !== 'object') return
  const key = makeNotificationFingerprint(payload)
  if (notificationDedupSet.has(key)) return
  if (notificationDedupSet.size > 512) {
    notificationDedupSet.clear()
  }
  notificationDedupSet.add(key)
  handleIncomingNotificationPayload(payload, origin)
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
  browserNotificationsEnabled,
  (enabled) => {
    if (
      enabled &&
      typeof Notification !== 'undefined' &&
      Notification.permission === 'default' &&
      !notificationPermissionRequestPending
    ) {
      notificationPermissionRequestPending = true
      Notification.requestPermission()
        .catch(() => {})
        .finally(() => {
          notificationPermissionRequestPending = false
        })
    }
  },
  { immediate: true },
)

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
    window.addEventListener('storage', handleBrowserPrefStorage)
    window.addEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
    window.addEventListener('cova:profile-update', handleProfileBroadcast)
    window.addEventListener('cova:notification-event', handleGlobalNotificationEvent)
    window.addEventListener('cova:open-conversation', handleExternalConversationRequest)
  }
  typingCleanupTimer = setInterval(cleanupRemoteTyping, 2000)
  syncBrowserNotificationPreference()
})



onBeforeUnmount(() => {
  endCall(true)
  disconnectRealtime()
  if (gifSearchTimer) {
    clearTimeout(gifSearchTimer)
  }
  toastTimers.forEach((timer) => clearTimeout(timer))
  toastTimers.clear()
  if (conversationNoticeTimer) {
    clearTimeout(conversationNoticeTimer)
    conversationNoticeTimer = null
  }
  if (typingCleanupTimer) {
    clearInterval(typingCleanupTimer)
    typingCleanupTimer = null
  }
  if (typeof window !== 'undefined') {
    document.removeEventListener('click', handleDocumentClick)
    document.removeEventListener('keydown', handleDocumentKeydown)
    window.removeEventListener('storage', handleBrowserPrefStorage)
    window.removeEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
    window.removeEventListener('cova:profile-update', handleProfileBroadcast)
    window.removeEventListener('cova:notification-event', handleGlobalNotificationEvent)
    window.removeEventListener('cova:open-conversation', handleExternalConversationRequest)
  }
})
</script>

<style src="@/assets/styles/messages.css"></style>

















