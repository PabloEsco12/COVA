<template>
  <section class="sidebar-profile mb-4">
    <div class="profile-avatar">
      <img
        v-if="avatarUrl"
        :src="avatarUrl"
        alt="Avatar utilisateur"
        width="48"
        height="48"
        class="rounded-circle"
        @error="$emit('avatar-error')"
      />
      <div v-else class="avatar-fallback">{{ initials }}</div>
    </div>
    <div class="profile-details">
      <div class="profile-heading">
        <h6 class="profile-name mb-0" :title="pseudo">{{ pseudo }}</h6>
        <span class="badge encryption-badge">
          <i class="bi bi-lock-fill me-1"></i>
          Chiffré
        </span>
      </div>
      <p class="profile-status-line">
        <span class="status-dot" :class="`status-${userStatusCode}`"></span>
        <span class="status-text">{{ userStatusLabel }}</span>
      </p>
      <p class="profile-connection" :class="{ 'is-offline': !isOnline }">
        {{ isOnline ? 'Connexion sécurisée' : 'Connexion instable' }}
      </p>
    </div>
  </section>
</template>

<script setup>
defineProps({
  pseudo: {
    type: String,
    default: 'Utilisateur',
  },
  avatarUrl: {
    type: String,
    default: null,
  },
  initials: {
    type: String,
    default: 'C',
  },
  userStatusCode: {
    type: String,
    default: 'available',
  },
  userStatusLabel: {
    type: String,
    default: 'Disponible',
  },
  isOnline: {
    type: Boolean,
    default: true,
  },
})

defineEmits(['avatar-error'])
</script>
