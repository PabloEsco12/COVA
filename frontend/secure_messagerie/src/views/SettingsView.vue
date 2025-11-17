<template>
  <div class="p-4">
    <h2 class="mb-4">
      <i class="bi bi-gear"></i> Parametres
    </h2>

    <!-- 1ère rangée : profil | sécurité -->
    <div class="row g-4">
      <div class="col-lg-6">
        <ProfileCard
          @profile-loaded="onProfileLoaded"
          @profile-updated="onProfileLoaded"
        />
      </div>

      <div class="col-lg-6">
        <SecurityCard />
      </div>
    </div>

    <hr class="my-5" />

    <!-- 2ème rangée : notifications | avatar -->
    <div class="row g-4">
      <div class="col-lg-6">
        <NotificationsCard />
      </div>
      <div class="col-lg-6">
        <AvatarCard
          :email="emailDisplay"
          :display-name="displayName"
          :avatar-url="avatarUrl"
          @avatar-updated="onAvatarUpdated"
        />
      </div>
    </div>

    <hr class="my-5" />

    <hr class="my-5" />

    <OrganizationAdministratorsCard class="mb-4" />

    <!-- zone dangereuse -->
    <DangerZone />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProfileCard from '@/components/settings/ProfileCard.vue'
import SecurityCard from '@/components/settings/SecurityCard.vue'
import NotificationsCard from '@/components/settings/NotificationsCard.vue'
import AvatarCard from '@/components/settings/AvatarCard.vue'
import DangerZone from '@/components/settings/DangerZone.vue'
import OrganizationAdministratorsCard from '@/components/settings/OrganizationAdministratorsCard.vue'

/**
 * Ces 3 infos servent à l’avatar (initiales) donc on les garde au niveau de la vue.
 * Le reste (API, appels) est dans les composants.
 */
const emailDisplay = ref('')
const displayName = ref('')
const avatarUrl = ref(null)

function onProfileLoaded(payload) {
  // payload vient du composant profil
  emailDisplay.value = payload.email || ''
  displayName.value = payload.display_name || ''
  if (payload.avatar_url) {
    avatarUrl.value = payload.avatar_url
  }
}

function onAvatarUpdated(newUrl) {
  avatarUrl.value = newUrl
}
</script>
