<template>
  <div class="dashboard-layout d-flex">
    <Sidebar class="sidebar" />
    <div class="flex-grow-1 d-flex flex-column min-vh-100">
      <DashboardHeader />
      <main class="flex-grow-1 bg-light px-3 py-4 main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import DashboardHeader from './DashboardHeader.vue'
import { useRouter, onMounted } from 'vue-router'

const router = useRouter()
onMounted(() => {
  if (!localStorage.getItem('access_token')) {
    router.push('/login')
  }
})
</script>

<style scoped>
.dashboard-layout {
  height: 100vh;
  background: linear-gradient(135deg, #eef3fc 0%, #e5ebf6 100%);
}
.main-content {
  background: #f7f9fb;
  border-radius: 20px;
  box-shadow: 0 4px 16px #1959c233;
}
.sidebar {
  min-width: 230px;
  background: #212529;
}
</style>
