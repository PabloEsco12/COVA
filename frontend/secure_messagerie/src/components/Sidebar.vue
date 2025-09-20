<template>
  <nav class="sidebar d-flex flex-column p-3">
    <router-link to="/dashboard" class="mb-4 text-center text-decoration-none">
      <img src="@/assets/logo_COVA.png" alt="COVA" width="48" />
      <h4 class="mt-2 text-light fw-bold">COVA</h4>
    </router-link>
    <ul class="nav nav-pills flex-column mb-auto">
      <li class="nav-item">
        <router-link to="/dashboard" class="nav-link" active-class="active">
          <i class="bi bi-house me-2"></i> Accueil
        </router-link>
      </li>
      <li>
        <router-link to="/dashboard/messages" class="nav-link" active-class="active">
          <i class="bi bi-chat-dots me-2"></i> Messages
          <span v-if="unreadCount > 0" class="badge bg-danger ms-2">{{ unreadCount }}</span>
        </router-link>
      </li>
      <li>
        <router-link to="/dashboard/contacts" class="nav-link" active-class="active">
          <i class="bi bi-people me-2"></i> Contacts
        </router-link>
      </li>
      <li>
        <router-link to="/dashboard/invitations" class="nav-link" active-class="active">
          <i class="bi bi-person-plus me-2"></i> Invitations
        </router-link>
      </li>
      <li>
        <router-link to="/dashboard/devices" class="nav-link" active-class="active">
          <i class="bi bi-phone me-2"></i> Appareils
        </router-link>
      </li>
      <li>
        <router-link to="/dashboard/settings" class="nav-link" active-class="active">
          <i class="bi bi-gear me-2"></i> Paramètres
        </router-link>
      </li>
    </ul>
    <div class="mt-auto text-center">
      <button
        class="btn btn-sm theme-toggle"
        :class="isDark ? 'btn-outline-light' : 'btn-outline-secondary'"
        @click="$emit('toggle-dark')"
      >
        <i :class="isDark ? 'bi bi-sun' : 'bi bi-moon'"></i>
        {{ isDark ? 'Clair' : 'Sombre' }}
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, defineProps, toRefs } from 'vue'
import axios from 'axios'

const props = defineProps({
  isDark: Boolean
})

const { isDark } = toRefs(props)

const unreadCount = ref(0)

onMounted(async () => {
  // Remplace l’URL par ta vraie route backend si dispo
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      const res = await axios.get('http://localhost:5000/api/messages/unread_count', {
        headers: { Authorization: `Bearer ${token}` }
      })
      unreadCount.value = res.data.count
    }
  } catch (e) {
    unreadCount.value = 0
  }
})
</script>

<style scoped>
.sidebar {
  min-width: 220px;
  background: linear-gradient(180deg, #212529 70%, #0d6efd 120%);
  position: sticky;   /* reste visible lors du scroll */
  top: 0;
  height: 100vh;      /* occupe toute la hauteur de la fenêtre */
  overflow-y: auto;   /* scroll interne si nécessaire */
}
.sidebar .nav-link {
  color: #d1d1d1;
}
.sidebar .nav-link.active,
.sidebar .nav-link.router-link-exact-active {
  background: #0d6efd;
  color: #fff;
}
.sidebar .mt-auto { position: sticky; bottom: 12px; }

.theme-toggle {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
</style>


