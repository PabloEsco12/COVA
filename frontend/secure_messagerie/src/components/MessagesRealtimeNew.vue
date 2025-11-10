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

      <aside class="msg-nav">

        <header class="msg-nav__header">

          <div>

            <p class="msg-nav__eyebrow">Chats</p>

            <h2>{{ conversationSummary }}</h2>

          </div>

          <button class="msg-nav__action" type="button" @click="goToNewConversation" :disabled="loadingConversations" aria-label="Nouvelle conversation">

            <i class="bi bi-pencil-square" aria-hidden="true"></i>

          </button>

        </header>

        <label class="msg-search">

          <i class="bi bi-search"></i>

          <input

            v-model.trim="conversationSearch"

            type="search"

            class="form-control form-control-sm"

            placeholder="Rechercher"

          />

        </label>

        <div class="msg-filters compact">

          <button

            v-for="filter in conversationFilters"

            :key="filter.value"

            type="button"

            class="msg-filter"

            :class="{ active: conversationFilter === filter.value }"

            @click="conversationFilter = filter.value"

          >

            {{ filter.label }}

          </button>

        </div>

        <p v-if="conversationError" class="msg-alert">{{ conversationError }}</p>

        <ul class="msg-nav__list">

          <li v-for="conversation in sortedConversations" :key="conversation.id">

            <button

              type="button"

              class="msg-nav__item"

              :class="{ active: conversation.id === selectedConversationId }"

              @click="selectConversation(conversation.id)"

            >

              <span class="msg-avatar">

                <img v-if="conversation.avatarUrl" :src="conversation.avatarUrl" alt="" @error="onAvatarFailure(conversation.id)" />

                <span v-else>{{ conversation.initials }}</span>

              </span>

              <span class="msg-item__body">

                <span class="msg-item__title">{{ conversation.displayName }}</span>

                <span class="msg-item__preview">{{ conversation.lastPreview || 'Aucun message' }}</span>

              </span>

              <span class="msg-item__meta">

                <time>{{ formatListTime(conversation.lastActivity) }}</time>

                <span v-if="conversation.unreadCount" class="msg-badge">{{ conversation.unreadCount }}</span>

              </span>

            </button>

          </li>

          <li v-if="!loadingConversations && !sortedConversations.length" class="msg-empty-row">

            <span>Aucune conversation</span>

          </li>

          <li v-if="loadingConversations" class="msg-empty-row">

            <span>Chargement.</span>

          </li>

        </ul>

      </aside>

<section class="msg-main">

            <div v-if="!selectedConversation" class="msg-empty">
        <h3>Messagerie sécurisée</h3>
        <p>Choisissez une conversation ou créez-en une nouvelle avec vos contacts vérifiés.</p>
        <button class="btn btn-primary" type="button" @click="goToNewConversation">Nouvelle conversation</button>
      </div>
<template v-else>

        <header class="msg-main__header">

          <div class="msg-main__identity">

            <span class="msg-main__avatar">

              <img v-if="selectedConversation.avatarUrl" :src="selectedConversation.avatarUrl" alt="" />

              <span v-else>{{ selectedConversation.initials }}</span>

            </span>

            <div>

              <h3>{{ selectedConversation.displayName }}</h3>

              <p class="msg-main__meta">{{ headerParticipants }}</p>

            </div>

          </div>

          <div class="msg-main__actions">

            <span class="msg-status__pill" :class="connectionStatusClass">{{ connectionStatusLabel }}</span>

            <button type="button" class="msg-main__icon" aria-label="Appel audio"><i class="bi bi-telephone"></i></button>

            <button type="button" class="msg-main__icon" aria-label="Appel vidéo"><i class="bi bi-camera-video"></i></button>

            <button type="button" class="msg-main__icon" aria-label="Informations" @click="openConversationPanel">
              <i class="bi bi-info-circle"></i>
            </button>
          </div>

        </header>
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
            <li v-if="!messageSearch.loading && !messageSearch.results.length && messageSearch.query" class="text-muted small">
              Aucun message trouvé.
            </li>
          </ul>
        </div>
        <div class="msg-body">
          <section v-if="pinnedMessages.length" class="msg-pinned card">

            <header class="msg-pinned__header">

              <i class="bi bi-bookmark-star-fill" aria-hidden="true"></i>

              <div>

                <strong>{{ pinnedMessages.length }} message{{ pinnedMessages.length > 1 ? 's' : '' }} épinglé{{ pinnedMessages.length > 1 ? 's' : '' }}</strong>

                <p class="mb-0 small text-muted">Gardez les consignes critiques à portée de main.</p>

              </div>

            </header>

            <ul class="msg-pinned__list">

              <li v-for="pin in pinnedMessages" :key="`pin-${pin.id}`">

                <button type="button" @click="scrollToMessage(pin.id)">

                  <span class="msg-pinned__time">{{ formatTime(pin.createdAt) }}</span>

                  <span class="msg-pinned__preview">{{ pin.preview }}</span>

                </button>

              </li>

            </ul>

          </section>

          <div ref="messageScroller" class="msg-thread" @scroll="onThreadScroll">
            <div v-if="loadingOlderMessages" class="msg-thread__loader">
              <span class="spinner-border spinner-border-sm me-2"></span>
              Chargement des messages précédents…
            </div>
            <article
              v-for="message in messages"
              :key="message.id"

              :id="`message-${message.id}`"

              class="msg-bubble"

              :class="{ me: message.sentByMe, system: message.isSystem, pinned: message.pinned, pending: message.localOnly }"

            >

              <header class="msg-bubble__meta">
                <div class="msg-bubble__identity">
                  <span>{{ message.displayName }}</span>
                  <span v-if="message.pinned" class="msg-pill">
                    <i class="bi bi-bookmark-fill" aria-hidden="true"></i>
                    épinglé
                  </span>
                  <span
                    v-if="messageSecurityLabel(message)"
                    class="msg-security-icon"
                    :title="messageSecurityTooltip(message)"
                  >
                    <i class="bi bi-shield-lock-fill" aria-hidden="true"></i>
                  </span>
                  <span v-if="message.editedAt && !message.deleted" class="msg-bubble__badge">Modifié</span>
                </div>
                <div class="msg-bubble__meta-aside">
                  <div class="msg-bubble__timestamps">
                    <span v-if="messageStatusLabel(message)" class="msg-state" :class="messageStatusClass(message)">{{ messageStatusLabel(message) }}</span>
                    <time :title="formatAbsolute(message.createdAt)">{{ formatTime(message.createdAt) }}</time>
                  </div>
                  <div
                    v-if="!message.deleted && !message.isSystem"
                    class="msg-bubble__toolbar"
                    @click.stop
                  >
                <button
                  type="button"
                  class="icon-btn subtle"
                  :aria-expanded="reactionPickerFor === message.id"
                  :aria-label="`Réagir au message de ${message.displayName}`"
                  @click.stop="toggleReactionPicker(message.id)"
                >
                  <i class="bi bi-emoji-smile"></i>
                </button>
                <button
                  type="button"
                  class="icon-btn subtle"
                  :aria-expanded="messageMenuOpen === message.id"
                  :aria-label="`Afficher les actions pour le message de ${message.displayName}`"
                  @click.stop="toggleMessageMenu(message.id)"
                >
                  <i class="bi bi-three-dots"></i>
                </button>
                <div
                  v-if="reactionPickerFor === message.id"
                  class="msg-popover msg-popover--reactions"
                  role="menu"
                  aria-label="Choisir une réaction"
                >
                  <button
                    v-for="emoji in reactionPalette"
                    :key="`${message.id}-picker-${emoji}`"
                    type="button"
                    class="msg-popover__item"
                    @click="handleReactionSelection(message, emoji)"
                    :disabled="isReactionPending(message.id, emoji)"
                  >
                    {{ emoji }}
                  </button>
                </div>
                <div
                  v-if="messageMenuOpen === message.id"
                  class="msg-popover msg-popover--menu"
                  role="menu"
                  aria-label="Actions du message"
                >
                  <button type="button" class="msg-menu__item" @click="copyMessage(message); closeTransientMenus()">
                    <i class="bi bi-clipboard"></i>
                    Copier
                  </button>
                  <button type="button" class="msg-menu__item" @click="startReply(message); closeTransientMenus()">
                    <i class="bi bi-reply"></i>
                    Répondre
                  </button>
                  <button type="button" class="msg-menu__item" @click="startForward(message); closeTransientMenus()">
                    <i class="bi bi-share"></i>
                    Transférer
                  </button>
                  <button
                    type="button"
                    class="msg-menu__item"
                    :disabled="isPinning(message.id)"
                    @click="handlePinToggle(message)"
                  >
                    <i :class="message.pinned ? 'bi bi-bookmark-fill' : 'bi bi-bookmark'"></i>
                    {{ message.pinned ? 'Retirer des favoris' : 'Épingler' }}
                  </button>
                  <button
                    v-if="message.sentByMe"
                    type="button"
                    class="msg-menu__item"
                    @click="startEdit(message); closeTransientMenus()"
                  >
                    <i class="bi bi-pencil-square"></i>
                    Modifier
                  </button>
                  <button
                    v-if="message.sentByMe || isConversationOwner"
                    type="button"
                    class="msg-menu__item text-danger"
                    @click="confirmDeleteMessage(message); closeTransientMenus()"
                  >
                    <i class="bi bi-trash"></i>
                    Supprimer
                  </button>
                </div>
                </div>
                </div>
              </header>

              <div v-if="message.replyTo" class="msg-reference msg-reference--reply">

                <p class="msg-reference__author">{{ message.replyTo.authorDisplayName || "Participant" }}</p>

                <p class="msg-reference__excerpt">

                  <span v-if="message.replyTo.deleted" class="text-muted">Message supprimé</span>

                  <span v-else>{{ message.replyTo.excerpt }}</span>

                </p>

              </div>

              <div v-if="message.forwardFrom" class="msg-reference msg-reference--forward">

                <p class="msg-reference__author">Transfert de {{ message.forwardFrom.authorDisplayName || "Participant" }}</p>

                <p class="msg-reference__excerpt">

                  <span v-if="message.forwardFrom.deleted" class="text-muted">Message supprimé</span>

                  <span v-else>{{ message.forwardFrom.excerpt }}</span>

                </p>

              </div>

              <div v-if="message.deleted" class="msg-bubble__deleted">Message supprimé</div>

              <template v-else>
<pre class="msg-bubble__body">{{ message.content }}</pre>

                <div v-if="message.attachments?.length" class="msg-attachments">

                  <article

                    v-for="attachment in message.attachments"

                    :key="attachment.id"

                    class="msg-attachment"

                  >

                    <div>

                      <strong>{{ attachment.fileName || 'Pièce jointe' }}</strong>

                      <p class="small mb-0 text-muted">

                        {{ attachment.mimeType || 'Fichier' }} · {{ formatFileSize(attachment.sizeBytes) }}

                      </p>

                    </div>

                    <button

                      type="button"

                      class="btn btn-link p-0"

                      :disabled="!attachment.downloadUrl"

                      @click="downloadAttachment(attachment)"

                    >

                      Télécharger

                    </button>

                  </article>

                </div>

                <div v-if="message.reactions && message.reactions.length" class="msg-reactions">

                  <button

                    v-for="reaction in message.reactions"

                    :key="`${message.id}-${reaction.emoji}`"

                    type="button"

                    class="msg-reaction"

                    :class="{ active: reaction.reacted }"

                    @click="toggleReaction(message, reaction.emoji)"

                    :disabled="isReactionPending(message.id, reaction.emoji)"

                  >

                    <span>{{ reaction.emoji }}</span>

                    <span>{{ reaction.count }}</span>

                  </button>

                </div>
                <p v-if="messageStatusDetail(message)" class="msg-bubble__note">
                  <i class="bi bi-clock-history" aria-hidden="true"></i>
                  <span>{{ messageStatusDetail(message) }}</span>
                </p>

</template>
<span v-if="copiedMessageId === message.id" class="msg-bubble__copied">Copié</span>

            </article>

            <div v-if="loadingMessages" class="msg-thread__loading">Chargement…</div>

          </div>

        </div>

        <form class="msg-composer" @submit.prevent="sendMessage">
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
                  Chargementâ€¦
                </div>
              </div>
            </div>
          </div>
          <input ref="attachmentInput" class="visually-hidden" type="file" multiple @change="onAttachmentChange" />
          <textarea
            v-model="messageInput"
            class="form-control"
            rows="2"
            placeholder="Écrire un message sécurisé."
            :disabled="sending"
            @keydown.enter.exact.prevent="sendMessage"
            @input="limitDraft"
          ></textarea>
          <div v-if="pendingAttachments.length && !isEditingMessage" class="msg-composer__attachments">
            <article v-for="attachment in pendingAttachments" :key="attachment.id" class="msg-composer__attachment">
              <div>
                <strong>{{ attachment.name }}</strong>
                <p class="small mb-0 text-muted">
                  {{ formatFileSize(attachment.size) }}
                  <span v-if="attachment.status === 'uploading'"> Â· {{ attachment.progress || 0 }}%</span>
                  <span v-if="attachment.status === 'error'" class="text-danger"> Â· {{ attachment.error }}</span>
                </p>
              </div>
              <div class="msg-composer__attachment-actions">
                <span v-if="attachment.status === 'uploading'" class="msg-panel__pill">Envoiâ€¦</span>
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
    <form class="msg-panel__section" @submit.prevent="saveConversationSettings">
      <div class="mb-3">
        <label class="form-label">Titre</label>
        <input v-model.trim="conversationForm.title" type="text" class="form-control" placeholder="Nom interne de la conversation" maxlength="160" />
      </div>
      <div class="mb-3">
        <label class="form-label">Sujet</label>
        <textarea v-model.trim="conversationForm.topic" class="form-control" rows="2" placeholder="Contexte ou consignes"></textarea>
      </div>
      <label class="form-check form-switch mb-3">
        <input v-model="conversationForm.archived" class="form-check-input" type="checkbox" />
        <span class="form-check-label">Conversation archivée</span>
      </label>
      <div class="d-flex gap-2">
        <button class="btn btn-primary flex-grow-1" type="submit" :disabled="savingConversation">
          <span v-if="savingConversation" class="spinner-border spinner-border-sm me-2"></span>
          Enregistrer
        </button>
        <button class="btn btn-outline-secondary" type="button" @click="closeConversationPanel">Fermer</button>
      </div>
    </form>
    <p v-if="conversationInfoError" class="msg-alert">{{ conversationInfoError }}</p>
    <button
      class="btn btn-outline-danger w-100 mb-3"
      type="button"
      @click="leaveCurrentConversation"
      :disabled="leavingConversation"
    >
      <span v-if="leavingConversation" class="spinner-border spinner-border-sm me-2"></span>
      Quitter la conversation
    </button>
    <section v-if="canManageConversation" class="msg-panel__section">
      <div class="msg-panel__section-header">
        <h5>Invitations</h5>
        <span v-if="loadingInvites" class="msg-panel__pill">Chargement</span>
      </div>
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
              {{ roleLabel(invite.role) }}
              <span v-if="formatInviteStatus(invite)"> Â· {{ formatInviteStatus(invite) }}</span>
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
      <ul class="msg-panel__list">
        <li v-for="member in selectedConversation.members" :key="member.id" class="msg-panel__member">
          <div>
            <strong>{{ member.displayName || member.email }}</strong>
            <p class="small mb-0 text-muted">
              {{ roleLabel(member.role) }}
              <span v-if="member.state !== 'active'"> Â· {{ member.state }}</span>
              <span v-if="member.mutedUntil" class="msg-panel__pill muted">
                Sourdine {{ formatAbsolute(member.mutedUntil) }}
              </span>
            </p>
          </div>
          <div v-if="canManageConversation && member.id !== (currentUserId || '')" class="msg-panel__member-actions">
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
</div>
</template>
<script setup>

import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import { useRoute, useRouter } from 'vue-router'
import { api } from '@/utils/api'
import { createConversationSocket } from '@/services/realtime'
import {
  pinMessage,
  unpinMessage,
  updateMessageReaction,
  uploadAttachment,
  editConversationMessage,
  deleteConversationMessage,
  searchConversationMessages,
  updateConversation,
  leaveConversation,
  updateConversationMember,
  listConversationInvites,
  createConversationInvite,
  revokeConversationInvite,
} from '@/services/conversations'
import { fetchGifs, hasGifApiSupport } from '@/services/media'


const emojiSections = [
  {
    id: 'trending',
    label: 'Émojis populaires',
    items: ['👍','✨','🎉','🔥','👏','😊','😍','🤝','🤔','🙏'],
  },
  {
    id: 'smileys',
    label: 'Smileys & émotions',
    items: [
      '😀','😄','😅','😂','🥰','😍','😎','🤩','😇','🤓','🙂','🙃','😉','🤗','🤔','😬','😢','😭','😡','😤','🤯','😴','😳','🥱','😐',
    ],
  },
  {
    id: 'gestures',
    label: 'Gestes & personnes',
    items: ['🤝','👍','👎','👏','🙌','🙏','👊','🤛','🤞','✌','🤘','🤟','👋','👌','🖖','👊','✊','🤏','🤲'],
  },
  {
    id: 'nature',
    label: 'Animaux & nature',
    items: ['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵','🐔','🐧','🐦','🐤'],
  },
  {
    id: 'food',
    label: 'Cuisine & boissons',
    items: ['🍏','🍎','🍊','🍉','🍓','🍇','🍒','🍑','🍍','🍏','🍅','🥑','🥦','🥕','🌽','🍔','🍕','🌭','🍟'],
  },
  {
    id: 'activities',
    label: 'Loisirs & voyages',
    items: ['⚽','🏀','🏈','⚾','🎾','🏐','🏉','🎱','🏓','🏸','🥅','🎣','🎿','🏂','🏋','🤸','🤼','🤽','🚴'],
  },
]
const emojiCatalog = emojiSections.flatMap((section) => section.items)

const gifLibrary = [

  { label: 'Bravo', url: 'https://media.giphy.com/media/111ebonMs90YLu/giphy.gif' },

  { label: 'Fête', url: 'https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif' },

  { label: 'Pouce', url: 'https://media.giphy.com/media/OkJat1YNdoD3W/giphy.gif' },

  { label: 'Applaudissements', url: 'https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif' },

  { label: 'Celebration', url: 'https://media.giphy.com/media/26gssIytJvy1b1THO/giphy.gif' },

  { label: 'LOL', url: 'https://media.giphy.com/media/l46CkATpdyLwLI7vi/giphy.gif' },

  { label: 'Love', url: 'https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif' },

  { label: 'ThumbsUp', url: 'https://media.giphy.com/media/l2SpQXcg3dYgP2QbS/giphy.gif' },

  { label: 'Party', url: 'https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif' },

  { label: 'Confetti', url: 'https://media.giphy.com/media/26u4hLUL3xFqj2iUU/giphy.gif' },

  { label: 'Wow', url: 'https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif' },

  { label: 'Happy Dance', url: 'https://media.giphy.com/media/Ju7l5y9osyymQ/giphy.gif' },

]



const conversations = ref([])

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
const pagination = reactive({
  beforeCursor: null,
  afterCursor: null,
  hasMoreBefore: false,
  hasMoreAfter: false,
})
const loadingOlderMessages = ref(false)
const suppressAutoScroll = ref(false)
const showSearchPanel = ref(false)
const messageSearch = reactive({
  query: '',
  results: [],
  loading: false,
  error: '',
})

const selectedConversationId = ref(null)
const messages = ref([])

const loadingMessages = ref(false)

const messageError = ref('')

const messageInput = ref('')

const sending = ref(false)

const copiedMessageId = ref(null)

const reactionPalette = ['\u{1F44D}', '\u{2705}', '\u{1F525}', '\u{26A0}', '\u{1F4A1}']

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
let notificationPermissionRequestPending = false
const browserNotificationsEnabled = ref(readBrowserNotificationPreference())


const socketRef = ref(null)

const connectionStatus = ref('idle')



let copyTimer = null
let gifSearchTimer = null


const route = useRoute()

const router = useRouter()

const messageScroller = ref(null)



const currentUserId = ref(localStorage.getItem('user_id') || null)
const authToken = ref(localStorage.getItem('access_token') || null)

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
  const id = member.user_id || member.id || member.member_id
  if (!id) return null
  const displayName = member.display_name || member.email || 'Membre'
  return {
    id: String(id),
    role: member.role || 'member',
    state: member.state || 'active',
    joinedAt: member.joined_at ? new Date(member.joined_at) : null,
    mutedUntil: member.muted_until ? new Date(member.muted_until) : null,
    displayName,
    email: member.email || '',
    avatarUrl: member.avatar_url || null,
    initials: computeInitials(displayName),
  }
}

function normalizeConversation(payload) {
  if (!payload) return null
  const members = Array.isArray(payload.members)
    ? payload.members.map((member) => normalizeMember(member)).filter(Boolean)
    : []
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  const activeParticipants = members.filter(
    (member) => member.state === 'active' && (!selfId || member.id !== selfId),
  )
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
    avatarUrl: payload.avatar_url || null,
  }
}
const conversationSummary = computed(() => {

  if (loadingConversations.value) return 'Chargementâ€¦'

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

const headerParticipants = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.participants)) return ''
  const names = conv.participants
    .map((participant) => participant.displayName || participant.email)
    .filter(Boolean)
  return names.join(', ')
})

const currentMembership = computed(() => {
  const conv = selectedConversation.value
  if (!conv || !Array.isArray(conv.members)) return null
  const selfId = currentUserId.value ? String(currentUserId.value) : null
  if (!selfId) return null
  return conv.members.find((member) => member.id === selfId) || null
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

    return {

      ...conv,

      unreadCount: meta.unreadCount || 0,

      lastPreview: meta.lastPreview || '',

      lastActivity: meta.lastActivity || conv.createdAt,

      avatarUrl: meta.avatarUrl ?? conv.avatarUrl ?? null,

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



const canSend = computed(() => {
  const value = messageInput.value.trim()
  const attachmentsReady = readyAttachments.value.length > 0 && !isEditingMessage.value
  return (Boolean(value) || attachmentsReady || composerState.mode === 'reply' || composerState.mode === 'forward') &&
    value.length <= 2000 &&
    Boolean(selectedConversationId.value)
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

      return 'Connexion…'

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

watch(selectedConversationId, (id) => {
  closeTransientMenus()
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
    if (!before) {
      const readableIds = list
        .filter((message) => !message.sentByMe && !message.isSystem && !message.deleted)
        .map((message) => message.id)
      if (readableIds.length) {
        await markConversationAsRead(conversationId, readableIds)
      } else if (reset) {
        await loadUnreadSummary()
      }
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
  return {
    id: String(payload.id || payload.message_id || generateLocalId()),
    conversationId: convId,
    authorId,
    displayName,
    avatarUrl: payload.author_avatar_url || null,
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
    preview: `${displayName}: ${content}`.trim(),
    attachments,
    editedAt,
    deletedAt,
    deleted,
    replyTo,
    forwardFrom,
    streamPosition,
  }
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
  messages.value = []
  disconnectRealtime()
  await loadMessages({ conversationId: id, reset: true })
  connectRealtime(id)
  if (!isSame) {
    await loadUnreadSummary()
  }
}

async function markConversationAsRead(convId, ids = []) {
  if (!convId) return

  const meta = ensureMeta(convId)

  meta.unreadCount = 0

  const body = ids && ids.length ? { message_ids: ids } : {}

  try {

    await api.post(`/conversations/${convId}/read`, body)

  } catch (err) {

    console.warn('Unable to synchroniser la lecture', err)

  }

  await loadUnreadSummary()

}



function incrementUnreadCounter(convId) {
  const meta = ensureMeta(convId)
  meta.unreadCount = (meta.unreadCount || 0) + 1
  const entries = unreadSummary.value.conversations.slice()
  const idx = entries.findIndex((entry) => entry.conversation_id === convId)
  if (idx >= 0) {

    entries[idx] = { ...entries[idx], unread: entries[idx].unread + 1 }

  } else {

    entries.push({ conversation_id: convId, unread: 1 })

  }

  unreadSummary.value = {
    total: unreadSummary.value.total + 1,
    conversations: entries,
  }
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
  target.participants = activeMembers.filter((member) => !selfId || member.id !== selfId)
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
  const payload = {
    content: draftContent,
    attachments: attachmentsPayload,
    reply_to_message_id: composerState.replyTo ? composerState.replyTo.id : null,
    forward_message_id: composerState.forwardFrom ? composerState.forwardFrom.id : null,
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
    messageError.value = extractError(err, "Impossible d'envoyer le message.")
  } finally {
    sending.value = false
  }
}

async function submitMessageEdit() {
  if (!selectedConversationId.value || !composerState.targetMessageId) return
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
  }
}


function connectRealtime(convId) {

  if (!authToken.value) {

    connectionStatus.value = 'idle'

    return

  }

  connectionStatus.value = 'connecting'

  socketRef.value = createConversationSocket(convId, {

    token: authToken.value,

    onOpen: () => (connectionStatus.value = 'connected'),

    onError: () => (connectionStatus.value = 'error'),

    onClose: () => (connectionStatus.value = 'idle'),

    onEvent: (payload) => {

      if (!payload || typeof payload !== 'object') return

      if (payload.event === 'ready') {

        connectionStatus.value = 'connected'

        return

      }

      if (payload.event === 'message' || payload.event === 'message.updated') {
        handleIncomingRealtime(payload)
      }
    },

  })

}



function disconnectRealtime() {
  if (socketRef.value) {
    socketRef.value.close()
    socketRef.value = null
  }
  connectionStatus.value = 'idle'
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

function onThreadScroll() {
  const el = messageScroller.value
  if (!el || loadingOlderMessages.value || !pagination.hasMoreBefore) return
  if (el.scrollTop < 120) {
    loadOlderMessages()
  }
}

function scrollToBottom() {
  const el = messageScroller.value
  if (el) el.scrollTop = el.scrollHeight
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

function toggleSearchPanel() {
  showSearchPanel.value = !showSearchPanel.value
  if (!showSearchPanel.value) {
    resetSearchPanel()
  }
}

function closeSearchPanel() {
  showSearchPanel.value = false
  resetSearchPanel()
}

function resetSearchPanel() {
  messageSearch.query = ''
  messageSearch.results = []
  messageSearch.error = ''
}

async function performMessageSearch() {
  if (!selectedConversationId.value) return
  const query = messageSearch.query.trim()
  if (!query) {
    messageSearch.error = 'Entrez un mot-clé.'
    messageSearch.results = []
    return
  }
  messageSearch.loading = true
  messageSearch.error = ''
  try {
    const data = await searchConversationMessages(selectedConversationId.value, { query, limit: 50 })
    messageSearch.results = Array.isArray(data) ? data.map(normalizeMessage) : []
  } catch (err) {
    messageSearch.error = extractError(err, 'Recherche impossible.')
  } finally {
    messageSearch.loading = false
  }
}

async function jumpToSearchResult(result) {
  if (!result) return
  if (result.conversationId && result.conversationId !== selectedConversationId.value) {
    await selectConversation(result.conversationId)
  }
  const streamPosition = result.streamPosition ?? null
  await ensureMessageVisible(result.id, streamPosition)
  await nextTick()
  scrollToMessage(result.id)
  showSearchPanel.value = false
  resetSearchPanel()
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

async function confirmDeleteMessage(message) {
  if (!message || !selectedConversationId.value) return
  const proceed = window.confirm('Supprimer ce message pour tous les participants ?')
  if (!proceed) return
  try {
    const data = await deleteConversationMessage(selectedConversationId.value, message.id)
    applyMessageUpdate(normalizeMessage(data))
  } catch (err) {
    messageError.value = extractError(err, "Impossible de supprimer le message.")
  }
}

function syncConversationFormFromSelected() {
  const conv = selectedConversation.value
  if (!conv) return
  conversationForm.title = conv.title || ''
  conversationForm.topic = conv.topic || ''
  conversationForm.archived = Boolean(conv.archived)
}

async function openConversationPanel() {
  if (!selectedConversation.value) return
  conversationInfoError.value = ''
  syncConversationFormFromSelected()
  showConversationPanel.value = true
  if (canManageConversation.value && selectedConversationId.value) {
    await loadConversationInvites(selectedConversationId.value)
  }
}

function closeConversationPanel() {
  showConversationPanel.value = false
  invites.value = []
}

async function saveConversationSettings() {
  if (!selectedConversationId.value) return
  savingConversation.value = true
  conversationInfoError.value = ''
  try {
    const payload = {
      title: conversationForm.title.trim() || null,
      topic: conversationForm.topic.trim() || null,
      archived: conversationForm.archived,
    }
    const data = await updateConversation(selectedConversationId.value, payload)
    applyConversationPatch(data)
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
  try {
    await revokeConversationInvite(selectedConversationId.value, inviteId)
    invites.value = invites.value.filter((invite) => invite.id !== inviteId)
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
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { role })
    applyMemberPayload(data)
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
  const mutedUntil = new Date(Date.now() + minutes * 60000).toISOString()
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: mutedUntil })
    applyMemberPayload(data)
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
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: null })
    applyMemberPayload(data)
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
  try {
    const data = await updateConversationMember(selectedConversationId.value, member.id, { state: 'left' })
    applyMemberPayload(data)
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
}

function insertGif(gif) {
  if (!gif?.url) return
  const base = messageInput.value ? `${messageInput.value.trim()} ` : ''
  messageInput.value = `${base}${gif.url} `
  showPicker.value = false
  gifSearch.value = ''
  gifError.value = ''
  limitDraft()
}




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



function queueToastNotification({ title, body, conversationId, messageId }) {
  const toast = {
    id: generateLocalId(),
    title: title || 'Nouveau message',
    body: body || '',
    conversationId,
    messageId,
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
}function triggerBrowserNotification(message, body) {
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
}function cloneComposerReference(target) {
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

  if (message.content) return String(message.content).slice(0, 120)

  if (Array.isArray(message.attachments) && message.attachments.length) {

    return `${message.attachments.length} piece(s) jointe(s)`

  }

  if (typeof message.attachments === 'number' && message.attachments > 0) {

    return `${message.attachments} piece(s) jointe(s)`

  }

  return ''

}



function messageStatusLabel(message) {

  if (!message.deliveryState) {

    return message.sentByMe ? 'Envoi' : ''

  }

  switch (message.deliveryState) {

    case 'read':

      return 'Lu'

    case 'delivered':

      return 'Distribué'

    case 'queued':

      return 'Envoi'

    default:

      return ''

  }

}



function messageStatusClass(message) {

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
  if (message.deleted) return 'Supprimé'
  if (!message.sentByMe) return ''
  if (message.readAt) {
    return `Lu ${formatTime(message.readAt)}`
  }
  if (message.deliveredAt) {

    return `Distribué ${formatTime(message.deliveredAt)}`

  }

  return ''

}



function messageSecurityLabel(message) {

  const scheme = message.security?.scheme || 'confidentiel'

  if (scheme === 'plaintext') return 'Chiffrage applicatif'

  return `Schéma ${scheme}`

}



function messageSecurityTooltip(message) {

  const metadata = message.security?.metadata || {}

  const lines = Object.entries(metadata).map(([key, value]) => `${key}: ${value}`)

  return [`Schéma: ${message.security?.scheme || 'n/a'}`, ...lines].join('\n')

}



function scrollToMessage(messageId) {

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



function handleDocumentClick() {
  if (!reactionPickerFor.value && !messageMenuOpen.value) return
  closeTransientMenus()
}



function handleDocumentKeydown(event) {
  if (event.key !== 'Escape') return
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

onMounted(async () => {
  await loadConversations()
  if (typeof window !== 'undefined') {
    document.addEventListener('click', handleDocumentClick)
    document.addEventListener('keydown', handleDocumentKeydown)
    window.addEventListener('storage', handleBrowserPrefStorage)
    window.addEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
  }
  syncBrowserNotificationPreference()
})



onBeforeUnmount(() => {
  disconnectRealtime()
  if (gifSearchTimer) {
    clearTimeout(gifSearchTimer)
  }
  toastTimers.forEach((timer) => clearTimeout(timer))
  toastTimers.clear()
  if (typeof window !== 'undefined') {
    document.removeEventListener('click', handleDocumentClick)
    document.removeEventListener('keydown', handleDocumentKeydown)
    window.removeEventListener('storage', handleBrowserPrefStorage)
    window.removeEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
  }
})
</script>

<style scoped>

.msg-shell {

  background: #eef1f8;

  padding: 1.25rem 1.5rem;

  border-radius: 32px;

  box-shadow: 0 25px 60px rgba(12, 24, 56, 0.08);

}



.msg-layout {

  display: grid;

  grid-template-columns: 280px minmax(0, 1fr);

  height: calc(100vh - 70px);

  background: transparent;

  column-gap: 1.25rem;

}



.msg-nav {

  background: #fff;

  border-right: none;

  display: flex;

  flex-direction: column;

  padding: 1.35rem 1.5rem;

  gap: 0.9rem;

  border-radius: 28px;

  box-shadow: 0 20px 50px rgba(15, 26, 48, 0.08);

  min-height: 0;

  height: 100%;

}



.msg-nav__header {

  display: flex;

  justify-content: space-between;

  align-items: flex-start;

  gap: 1rem;

}



.msg-nav__eyebrow {

  text-transform: uppercase;

  font-size: 0.78rem;

  letter-spacing: 0.08em;

  color: #7f8ca8;

  margin-bottom: 0.15rem;

}



.msg-nav__header h2 {

  font-size: 1.4rem;

  font-weight: 700;

  margin-bottom: 0.2rem;

}



.msg-nav__header p {

  margin: 0;

  font-size: 0.82rem;

  color: #6d7894;

}



.msg-nav__action {

  width: 40px;

  height: 40px;

  border-radius: 12px;

  border: none;

  background: #eef3ff;

  color: #1b64f2;

  display: grid;

  place-items: center;

  font-size: 1.1rem;

}

.msg-search {

  position: relative;

  display: block;

}



.msg-search i {

  position: absolute;

  left: 0.75rem;

  top: 50%;

  transform: translateY(-50%);

  color: #9aa4be;

}



.msg-search input {

  padding-left: 2.2rem;

  border-radius: 999px;

  border: 1px solid #d3daeb;

}



.msg-alert {

  background: #fff4cd;

  border-radius: 12px;

  padding: 0.6rem 0.9rem;

  font-size: 0.82rem;

  color: #7c6225;

}



.msg-filters {

  display: flex;

  gap: 0.35rem;

  flex-wrap: wrap;

}



.msg-filters.compact {

  justify-content: space-between;

}



.msg-filter {

  border: 1px solid #d9e2f4;

  border-radius: 999px;

  padding: 0.25rem 0.8rem;

  font-size: 0.78rem;

  display: inline-flex;

  align-items: center;

  gap: 0.35rem;

  background: transparent;

  color: #4a5773;

  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;

}



.msg-filter.active {

  background: #1b64f2;

  color: #fff;

  border-color: #1b64f2;

  box-shadow: 0 8px 18px rgba(27, 100, 242, 0.2);

}

.msg-nav__list {

  list-style: none;

  margin: 0;

  padding: 0 0.35rem 1rem 0;

  flex: 1;

  overflow-y: auto;

  display: flex;

  flex-direction: column;

  gap: 0.35rem;

}



.msg-nav__item {

  width: 100%;

  border: none;

  background: transparent;

  display: grid;

  grid-template-columns: auto 1fr auto;

  gap: 0.75rem;

  align-items: center;

  padding: 0.55rem 0.65rem;

  border-radius: 18px;

  transition: background 0.15s ease;

}



.msg-nav__item:hover {

  background: #f5f8ff;

}



.msg-nav__item.active {

  background: #e6eeff;

}



.msg-avatar {

  width: 46px;

  height: 46px;

  border-radius: 50%;

  background: #eef2ff;

  display: grid;

  place-items: center;

  color: #1b64f2;

  font-weight: 600;

  overflow: hidden;

}



.msg-avatar img {

  width: 100%;

  height: 100%;

  object-fit: cover;

}



.msg-item__body {

  display: flex;

  flex-direction: column;

  gap: 0.15rem;

}



.msg-item__title {

  font-weight: 600;

  color: #13224b;

  font-size: 0.92rem;

}



.msg-item__preview {

  font-size: 0.78rem;

  color: #7e8aa8;

  white-space: nowrap;

  overflow: hidden;

  text-overflow: ellipsis;

}



.msg-item__meta {

  display: flex;

  flex-direction: column;

  align-items: flex-end;

  gap: 0.25rem;

  font-size: 0.7rem;

  color: #7f8ca8;

}

.msg-badge {

  background: #ff6b6b;

  color: #fff;

  border-radius: 999px;

  padding: 0.1rem 0.45rem;

  font-size: 0.7rem;

  font-weight: 600;

}



.msg-empty-row {

  text-align: center;

  font-size: 0.82rem;

  color: #6d7894;

  padding: 0.6rem 0;

}



.msg-main {

  background: linear-gradient(180deg, #f2f6ff 0%, #e7ecfb 40%, #f8f9ff 100%);

  display: flex;

  flex-direction: column;

  position: relative;

  min-height: 0;

  border-radius: 30px;

  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7), 0 20px 45px rgba(15, 26, 48, 0.06);

}



.msg-body {

  flex: 1;

  display: flex;

  flex-direction: column;

  min-height: 0;

  overflow: hidden;

  padding: 0 2.25rem 1.25rem;

  gap: 1rem;

}



.msg-empty {

  margin: auto;

  max-width: 420px;

  text-align: center;

  background: #fff;

  padding: 2rem;

  border-radius: 20px;

  box-shadow: 0 15px 40px rgba(15, 26, 48, 0.08);

}



.msg-empty h3 {

  font-weight: 700;

  margin-bottom: 0.75rem;

}



.msg-empty p {

  color: #6d7894;

  margin-bottom: 1.25rem;

}



.msg-main__header {

  padding: 1.75rem 2rem 1.25rem;

  display: flex;

  justify-content: space-between;

  align-items: center;

  gap: 1rem;

  border-bottom: 1px solid rgba(13, 110, 253, 0.1);

}



.msg-main__identity {

  display: flex;

  align-items: center;

  gap: 0.85rem;

}



.msg-main__avatar {

  width: 48px;

  height: 48px;

  border-radius: 50%;

  background: #e4eaff;

  display: grid;

  place-items: center;

  font-weight: 600;

  color: #1b64f2;

  overflow: hidden;

}



.msg-main__avatar img {

  width: 100%;

  height: 100%;

  object-fit: cover;

}



.msg-main__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.msg-search-panel {
  background: #f8fafc;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  padding: 0.75rem 1rem;
  margin: 0 1.5rem 1rem;
}

.msg-search-panel__form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.msg-search-results {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.msg-search-results__item {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.4rem 0.25rem;
  border-bottom: 1px dashed #e2e8f0;
}

.msg-search__author {
  font-weight: 600;
  margin: 0;
  font-size: 0.85rem;
}

.msg-search__excerpt {
  margin: 0;
  font-size: 0.8rem;
  color: #475569;
}


.msg-main__icon {

  width: 38px;

  height: 38px;

  border-radius: 12px;

  border: none;

  background: rgba(19, 34, 75, 0.08);

  color: #1b243d;

  display: grid;

  place-items: center;

  font-size: 1rem;

}



.msg-status__pill {

  padding: 0.25rem 0.75rem;

  border-radius: 999px;

  font-size: 0.72rem;

  text-transform: uppercase;

  letter-spacing: 0.06em;

}

.msg-main__header h3 {

  margin: 0 0 0.35rem;

  font-weight: 700;

  font-size: 1.45rem;

  line-height: 1.2;

}



.msg-main__meta {

  margin: 0;

  font-size: 0.82rem;

  color: #6d7894;

}



.msg-status {

  display: flex;

  align-items: center;

  gap: 0.4rem;

  font-size: 0.8rem;

  color: #6d7894;

}



.msg-status__dot {

  width: 10px;

  height: 10px;

  border-radius: 50%;

}



.msg-status__dot.ok {

  background: #31c48d;

  box-shadow: 0 0 0 4px rgba(49, 196, 141, 0.15);

}



.msg-status__dot.pending {

  background: #f8c924;

  box-shadow: 0 0 0 4px rgba(248, 201, 36, 0.15);

}



.msg-status__dot.error {

  background: #ff6b6b;

  box-shadow: 0 0 0 4px rgba(255, 107, 107, 0.15);

}



.msg-pinned {

  border-radius: 18px;

  padding: 1rem 1.25rem;

  border: 1px solid rgba(13, 110, 253, 0.12);

  margin-bottom: 0.75rem;

  background: #fff;

}



.msg-pinned__header {

  display: flex;

  align-items: center;

  gap: 0.75rem;

  margin-bottom: 0.75rem;

}



.msg-pinned__header i {

  font-size: 1.3rem;

  color: #d69000;

}



.msg-pinned__list {

  list-style: none;

  padding: 0;

  margin: 0;

  display: flex;

  flex-direction: column;

  gap: 0.4rem;

}



.msg-pinned__list button {

  width: 100%;

  text-align: left;

  border: 1px dashed rgba(13, 110, 253, 0.25);

  border-radius: 12px;

  padding: 0.45rem 0.75rem;

  background: rgba(13, 110, 253, 0.05);

  display: flex;

  gap: 0.75rem;

  align-items: center;

  transition: background 0.15s ease, border-color 0.15s ease;

}



.msg-pinned__list button:hover {

  background: rgba(13, 110, 253, 0.1);

  border-color: rgba(13, 110, 253, 0.5);

}



.msg-pinned__time {

  font-size: 0.78rem;

  color: #6d7894;

  min-width: 56px;

}



.msg-pinned__preview {

  font-size: 0.88rem;

  color: #182135;

  white-space: nowrap;

  overflow: hidden;

  text-overflow: ellipsis;

}

.msg-thread__loading {

  text-align: center;

  color: #6d7894;

  font-size: 0.82rem;

}



.msg-bubble {
  align-self: flex-start;
  max-width: min(52ch, 78%);
  background: radial-gradient(circle at 20% 20%, #ffffff 0%, #f7f9fd 55%, #eff3fb 100%);
  border-radius: 22px;
  padding: 1rem 1.2rem 0.9rem;
  border: 1px solid rgba(15, 23, 42, 0.05);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
  position: relative;
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  color: #1e2746;
}

.msg-bubble.pinned {
  border-color: rgba(245, 158, 11, 0.5);
  box-shadow: 0 24px 40px rgba(245, 158, 11, 0.18);
}

.msg-bubble--focus {
  animation: bubble-focus 1s ease;
}

@keyframes bubble-focus {
  0% {
    box-shadow: 0 0 0 0 rgba(21, 84, 246, 0.35);
  }
  100% {
    box-shadow: 0 0 0 26px rgba(21, 84, 246, 0);
  }
}

.msg-bubble.me {
  align-self: flex-end;
  background: linear-gradient(140deg, #2236c7, #4b6cff 45%, #66b1ff);
  color: #f3f7ff;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 28px 45px rgba(20, 60, 190, 0.35);
}

.msg-bubble.me::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 20px;
  background: linear-gradient(140deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0));
  pointer-events: none;
}

.msg-bubble.me > * {
  position: relative;
  z-index: 1;
}

.msg-bubble.pending {
  opacity: 0.9;
}

.msg-bubble.me.pending {
  box-shadow: 0 24px 45px rgba(20, 60, 190, 0.25);
}

.msg-bubble.system {
  font-style: italic;
  background: rgba(15, 23, 42, 0.06);
  color: #0f172a;
  border-style: dashed;
}

.msg-bubble__meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.45rem;
  gap: 0.75rem;
}

.msg-bubble__identity {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  color: #2b3560;
}

.msg-security-icon {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #e0f2fe;
  color: #0369a1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.msg-bubble.me .msg-security-icon {
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
}

.msg-bubble__meta-aside {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.msg-bubble.me .msg-bubble__identity,
.msg-bubble.me .msg-bubble__meta,
.msg-bubble.me .msg-bubble__meta span {
  color: rgba(243, 247, 255, 0.92);
}

.msg-bubble.me time {
  color: rgba(255, 255, 255, 0.85);
}

.msg-pill {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #d97706;
  background: rgba(217, 119, 6, 0.15);
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
  font-weight: 600;
}

.msg-bubble__timestamps {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
  text-align: right;
}

.msg-state {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  border: none;
  background: rgba(100, 116, 139, 0.15);
  color: #475569;
  font-weight: 600;
}

.msg-state.state-read {
  background: rgba(34, 197, 94, 0.2);
  color: #059669;
}

.msg-state.state-delivered {
  background: rgba(59, 130, 246, 0.2);
  color: #1d4ed8;
}

.msg-state.state-queued {
  background: rgba(234, 179, 8, 0.2);
  color: #b45309;
}

.msg-bubble.me .msg-state {
  background: rgba(255, 255, 255, 0.25);
  color: #fefefe;
}

.msg-bubble__body {
  margin: 0;
  white-space: pre-wrap;
  font-size: 0.95rem;
  line-height: 1.55;
  color: #0f172a;
}

.msg-bubble.me .msg-bubble__body {
  color: #f8fbff;
  text-shadow: 0 1px 2px rgba(18, 53, 143, 0.35);
}

.msg-bubble__toolbar {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.msg-bubble:hover .msg-bubble__toolbar,
.msg-bubble:focus-within .msg-bubble__toolbar,
.msg-bubble__toolbar:focus-within {
  opacity: 1;
  transform: translateY(0);
}

@media (hover: none) {
  .msg-bubble__toolbar {
    opacity: 1;
    transform: none;
  }
}

.icon-btn {
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: #fff;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  color: #475569;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.icon-btn:hover {
  background: #eff4ff;
  border-color: rgba(21, 84, 246, 0.4);
  color: #1554f6;
}

.icon-btn.subtle {
  background: rgba(255, 255, 255, 0.9);
}

.msg-bubble.me .icon-btn.subtle {
  background: rgba(255, 255, 255, 0.18);
  border-color: transparent;
  color: #fff;
}

.msg-bubble__copied {
  font-size: 0.72rem;
  color: #94a3b8;
  display: inline-block;
  margin-top: 0.15rem;
}

.msg-reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.35rem;
}

.msg-reaction {
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(148, 163, 184, 0.12);
  border-radius: 999px;
  padding: 0.15rem 0.55rem;
  font-size: 0.78rem;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: #0f172a;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.msg-reaction.active {
  border-color: rgba(21, 84, 246, 0.9);
  background: rgba(21, 84, 246, 0.12);
  color: #1554f6;
}

.msg-bubble.me .msg-reaction {
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.msg-popover {
  position: absolute;
  top: calc(100% + 0.4rem);
  right: 0;
  background: #fff;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.16);
  padding: 0.45rem;
  z-index: 5;
  min-width: 140px;
}

.msg-popover--reactions {
  display: flex;
  gap: 0.35rem;
}

.msg-popover--menu {
  min-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.msg-popover__item {
  border: none;
  background: transparent;
  font-size: 1.15rem;
  line-height: 1;
  cursor: pointer;
}

.msg-popover__item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.msg-menu__item {
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.84rem;
  color: #0f172a;
  padding: 0.25rem 0.15rem;
  text-align: left;
  border-radius: 8px;
}

.msg-menu__item:hover {
  background: rgba(21, 84, 246, 0.08);
  color: #1554f6;
}

.msg-menu__item i {
  font-size: 0.95rem;
}

.msg-menu__item.text-danger {
  color: #dc2626;
}

.msg-menu__item.text-danger:hover {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
}

.msg-bubble__note {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.msg-bubble.me .msg-bubble__note {
  color: rgba(255, 255, 255, 0.8);
}


.msg-attachments {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.4rem;
}

.msg-reference {
  background: #f0f3fb;
  border-left: 3px solid #9dabce;
  border-radius: 10px;
  padding: 0.45rem 0.75rem;
  margin-bottom: 0.45rem;
}

.msg-reference--forward {
  border-left-color: #3a8be8;
}

.msg-reference__author {
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 0.1rem;
  color: #1f2b49;
}

.msg-reference__excerpt {
  font-size: 0.76rem;
  color: #475569;
  margin: 0;
}

.msg-attachment {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.65rem;
  background: #f1f5f9;
  border-radius: 12px;
  padding: 0.3rem 0.75rem;
  font-size: 0.85rem;
}

.msg-bubble__deleted {
  font-style: italic;
  color: #7c8aa8;
  padding: 0.55rem 0.9rem;
  background: rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  border: 1px dashed rgba(146, 155, 173, 0.55);
  letter-spacing: 0.015em;
  text-align: center;
}

.msg-bubble.me .msg-bubble__deleted {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.55);
}

.msg-bubble__badge {
  background: #fef9c3;
  color: #854d0e;
  font-size: 0.7rem;
  padding: 0.05rem 0.45rem;
  border-radius: 999px;
  margin-left: 0.4rem;
}



.msg-composer {
  background: linear-gradient(180deg, #f9fbff 0%, #ffffff 60%);
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  padding: 1.2rem 1.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  border-bottom-left-radius: 28px;
  border-bottom-right-radius: 28px;
}

.msg-composer textarea {
  resize: none;
  border-radius: 18px;
  border: 1px solid #d3daeb;
  padding: 1rem 1.15rem;
  min-height: 110px;
  font-size: 0.95rem;
  line-height: 1.5;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
  background: #fdfdff;
}

.msg-composer textarea:focus {
  border-color: #1554f6;
  box-shadow: 0 0 0 3px rgba(21, 84, 246, 0.15);
  background: #ffffff;
}

.msg-composer__pickers {
  position: relative;
}

.msg-picker {
  position: absolute;
  bottom: calc(100% + 0.9rem);
  right: 0;
  width: min(520px, 92vw);
  background: #fff;
  border-radius: 22px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 35px 80px rgba(15, 23, 42, 0.25);
  padding: 1.1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  z-index: 30;
}

.msg-picker__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.msg-picker__tabs {
  display: inline-flex;
  background: #eef2fb;
  border-radius: 14px;
  padding: 0.2rem;
  gap: 0.15rem;
}

.msg-picker__tabs button {
  border: none;
  background: transparent;
  color: #64748b;
  font-weight: 600;
  padding: 0.35rem 1rem;
  border-radius: 12px;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}

.msg-picker__tabs button.active {
  background: #fff;
  color: #1b4ed5;
  box-shadow: 0 6px 14px rgba(27, 78, 213, 0.2);
}

.msg-picker__search {
  flex: 1;
  border: 1px solid #d3daeb;
  border-radius: 999px;
  padding: 0.4rem 0.95rem;
  font-size: 0.92rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.msg-picker__search:focus {
  border-color: #1554f6;
  box-shadow: 0 0 0 3px rgba(21, 84, 246, 0.12);
  outline: none;
}

.msg-picker__body {
  max-height: 280px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-right: 0.3rem;
}

.msg-picker__body::-webkit-scrollbar {
  width: 6px;
}

.msg-picker__body::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.25);
  border-radius: 999px;
}

.msg-picker__section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.msg-picker__section-title {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
  font-weight: 600;
}

.msg-picker__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
  gap: 0.25rem;
}

.msg-picker__grid button {
  border: none;
  background: #f6f7fb;
  border-radius: 12px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  cursor: pointer;
  transition: transform 0.1s ease, background 0.1s ease, box-shadow 0.1s ease;
}

.msg-picker__grid button:hover,
.msg-picker__grid button:focus-visible {
  background: #e8edff;
  box-shadow: 0 6px 12px rgba(21, 84, 246, 0.15);
  transform: translateY(-2px);
  outline: none;
}

.msg-picker__body--gifs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.75rem;
  max-height: 320px;
  overflow-y: auto;
}

.msg-picker__body--gifs button {
  border: none;
  background: #f5f7fb;
  border-radius: 16px;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  text-align: left;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.msg-picker__body--gifs button img {
  width: 100%;
  height: 96px;
  object-fit: cover;
}

.msg-picker__body--gifs button span {
  padding: 0.45rem 0.75rem 0.65rem;
  font-size: 0.78rem;
  color: #475569;
}

.msg-picker__body--gifs button:hover,
.msg-picker__body--gifs button:focus-visible {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px rgba(15, 23, 42, 0.15);
  outline: none;
}

.msg-picker__hint {
  font-size: 0.82rem;
  color: #94a3b8;
  margin: 0;
}

.msg-picker__error {
  color: #c2410c;
  font-size: 0.85rem;
  text-align: center;
}

.msg-picker__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: #64748b;
}

.msg-toast-stack {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  z-index: 5000;
  pointer-events: none;
}

.msg-toast {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.25);
  padding: 0.8rem 1rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
  pointer-events: auto;
}

.msg-toast__content {
  flex: 1;
}

.msg-toast__title {
  font-weight: 700;
  font-size: 0.92rem;
  margin: 0;
  color: #0f172a;
}

.msg-toast__body {
  margin: 0.15rem 0 0.25rem;
  font-size: 0.85rem;
  color: #475569;
}

.msg-toast small {
  font-size: 0.75rem;
  color: #94a3b8;
}

.msg-toast__close {
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 0.9rem;
  padding: 0.2rem;
}

.msg-toast-enter-active,
.msg-toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.msg-toast-enter-from,
.msg-toast-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.msg-composer__footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  font-size: 0.82rem;
  color: #6d7894;
}

.msg-composer__left {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.msg-composer__actions {
  display: inline-flex;
  gap: 0.4rem;
}

.msg-icon-btn {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: #ffffff;
  color: #1b4ed5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.msg-icon-btn:hover {
  background: #edf2ff;
  border-color: rgba(27, 100, 242, 0.4);
}

.msg-icon-btn.primary {
  border: none;
  background: linear-gradient(135deg, #1c6bff, #559dff);
  color: #fff;
  box-shadow: 0 8px 16px rgba(28, 107, 255, 0.25);
}

.msg-icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.msg-composer small {
  color: #94a3b8;
}

.msg-composer textarea::placeholder {
  color: #9aa5ba;
}

@media (max-width: 768px) {
  .msg-picker {
    left: 50%;
    right: auto;
    transform: translateX(-50%);
    width: min(520px, 95vw);
  }
}

@media (max-width: 480px) {
  .msg-picker {
    padding: 0.9rem;
    border-radius: 18px;
  }
  .msg-picker__header {
    flex-direction: column;
    align-items: stretch;
  }
  .msg-picker__tabs {
    width: 100%;
    justify-content: center;
  }
}



.msg-body::after {

  content: '';

  display: block;

  height: 0.5rem;

  flex-shrink: 0;

}





.msg-status__pill.ok {

  background: rgba(49, 196, 141, 0.15);

  color: #1c8a62;

}



.msg-status__pill.pending {

  background: rgba(248, 201, 36, 0.15);

  color: #b88600;

}



.msg-status__pill.error {

  background: rgba(255, 107, 107, 0.15);

  color: #a82323;

}

.msg-thread {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.msg-thread__loader {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.85rem;
  padding-bottom: 0.5rem;
}

.msg-panel {
  position: fixed;
  top: 2rem;
  right: 2rem;
  width: 360px;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 25px 60px rgba(15, 26, 48, 0.15);
  padding: 1.5rem;
  z-index: 20;
}

.msg-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.msg-panel__eyebrow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
  margin-bottom: 0.2rem;
}

.msg-panel__subtitle {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.9rem;
}

.msg-panel__close {
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 1.2rem;
  line-height: 1;
}

.msg-panel__section {
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
  margin-bottom: 1.5rem;
}

.msg-panel__section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.msg-panel__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.msg-panel__list-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
}

.msg-panel__member {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
}

.msg-panel__member-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  min-width: 150px;
}

.msg-panel__pill {
  display: inline-flex;
  align-items: center;
  background: #eef2ff;
  color: #4338ca;
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  font-size: 0.75rem;
}

.msg-panel__pill.muted {
  background: #fff7ed;
  color: #c2410c;
}

.msg-panel__pill.ok {
  background: #ecfdf5;
  color: #0f9e5e;
}

.msg-panel__invite-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.msg-panel__invite-row {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 1200px) {
  .msg-panel {
    position: fixed;
    inset: 0.5rem;
    width: auto;
    max-height: calc(100vh - 1rem);
  }
}

@media (max-width: 1200px) {
  .msg-layout {

    padding: 1rem;

  }



  .msg-body {

    padding: 0 1.5rem 1rem;

  }



  .msg-main__header {

    padding: 1.5rem 1.5rem 1rem;

  }

}



@media (min-width: 1600px) {

  .msg-layout {

    max-width: 1700px;

    grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);

    padding: 2rem 2.5rem;

  }



  .msg-body {

    padding: 0 3rem 1.5rem;

  }



  .msg-main__header {

    padding-left: 2.5rem;

    padding-right: 2.5rem;

  }

}



@media (max-width: 992px) {

  .msg-layout {

    grid-template-columns: 1fr;

    height: auto;

    padding: 0;

    border-radius: 0;

  }



  .msg-nav {

    border-right: none;

    border-bottom: 1px solid #e3e8f5;

    border-radius: 0;

    box-shadow: none;

    padding: 1.25rem;

  }



  .msg-main {

    border-radius: 0;

  }



  .msg-body {

    padding: 0 1rem 1rem;

  }

}



@media (max-width: 576px) {

  .msg-nav {

    padding: 1rem;

  }



  .msg-overview {

    grid-template-columns: 1fr;

  }



  .msg-main__header {

    flex-direction: column;

    align-items: flex-start;

  }



  .msg-composer {

    padding: 1rem;

  }

}

</style>



































