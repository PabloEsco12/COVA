?<template>

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
import { useMessagesView } from './messages/useMessagesView'

const {
  myAvailability,
  deleteDialog,
  deleteDialogPreview,
  conversationSearch,
  loadingConversations,
  conversationError,
  conversationFilter,
  conversationFilters,
  conversationRoles,
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
  pendingAttachments,
  attachmentError,
  composerState,
  forwardPicker,
  loadingOlderMessages,
  selectedConversationId,
  messages,
  loadingMessages,
  messageError,
  messageInput,
  sending,
  copiedMessageId,
  reactionPalette,
  reactionPickerFor,
  messageMenuOpen,
  showPicker,
  pickerMode,
  loadingGifs,
  gifError,
  gifSearchAvailable,
  messageToasts,
  callState,
  callControls,
  connectionStatus,
  currentUserId,
  initials,
  userId,
  displayName,
  avatarUrl,
  members,
  createdAt,
  conversationSummary,
  filteredEmojiSections,
  displayedGifs,
  selectedConversation,
  composerBlockedInfo,
  conversationOwnerSummary,
  target,
  headerSubtitle,
  primaryParticipantPresence,
  typingIndicatorText,
  remoteDisplayName,
  callStatusLabel,
  isConversationOwner,
  canManageConversation,
  hasAttachmentInProgress,
  isEditingMessage,
  hasComposerContext,
  canSend,
  value,
  pinnedMessages,
  sortedConversations,
  forwardPickerTargets,
  participantsLabel,
  replyTo,
  forwardFrom,
  selectConversation,
  id,
  body,
  roleLabel,
  memberPresence,
  member,
  status,
  label,
  memberPresenceText,
  onComposerInput,
  handleComposerBlur,
  message,
  goToNewConversation,
  onAvailabilityChange,
  togglePicker,
  setPickerMode,
  initiateForward,
  cancelForwardSelection,
  confirmForwardTarget,
  startReply,
  startEdit,
  cancelComposerContext,
  triggerAttachmentPicker,
  onAttachmentChange,
  removeAttachment,
  confirmDeleteMessage,
  closeDeleteDialog,
  performDeleteMessage,
  openConversationPanel,
  closeConversationPanel,
  leaveCurrentConversation,
  revokeInvite,
  updateMemberRole,
  muteMember,
  mutedUntil,
  unmuteMember,
  removeMember,
  addEmoji,
  insertGif,
  startCall,
  cancelOutgoingCall,
  hangupCall,
  rejectIncomingCall,
  acceptIncomingCall,
  toggleMicrophone,
  toggleCamera,
  copyMessage,
  toast,
  openToastConversation,
  preview,
  title,
  isPinning,
  isReactionPending,
  handlePinToggle,
  formatTime,
  formatAbsolute,
  formatFileSize,
  size,
  messagePreviewText,
  messageFormatters,
} = useMessagesView();
</script>


<style src="@/assets/styles/messages.css"></style>


















