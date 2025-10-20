<template>
  <div class="dashboard-layout d-flex" :class="{ 'dashboard-layout-dark': isDark }">
    <Sidebar :is-dark="isDark" @toggle-dark="toggleTheme" />
    <div class="flex-grow-1 d-flex flex-column min-vh-100">
      <DashboardHeader :is-dark="isDark" @toggle-dark="toggleTheme" />
      <main
        class="flex-grow-1 px-3 py-4 main-content"
        :class="{ 'main-content-dark': isDark }"
      >
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import DashboardHeader from './DashboardHeader.vue'
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'

const router = useRouter()

const isDark = ref(document.body.classList.contains('dark-mode'))

const applyTheme = (dark) => {
  isDark.value = dark
  document.body.classList.toggle('dark-mode', dark)
  document.body.classList.toggle('light-mode', !dark)
  try {
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  } catch (err) {
    console.warn('Unable to persist theme preference', err)
  }
}

const toggleTheme = () => {
  applyTheme(!isDark.value)
}

onMounted(() => {
  if (!localStorage.getItem('access_token')) {
    router.push('/login')
  }

  try {
    const saved = localStorage.getItem('theme')
    if (saved) {
      applyTheme(saved === 'dark')
    } else {
      applyTheme(isDark.value)
    }
  } catch {
    applyTheme(isDark.value)
  }
})
</script>

<style scoped src="../styles/components/Dashboard.css"></style>
