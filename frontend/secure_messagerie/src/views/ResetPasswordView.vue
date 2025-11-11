<!-- src/views/ResetPasswordView.vue -->
<template>
  <div class="auth-page reset-page">
    <!-- on laisse le décor ici -->
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>

    <ResetPasswordForm />
  </div>
</template>

<script setup>
import ResetPasswordForm from '@/components/auth/ResetPasswordForm.vue'
</script>

<style scoped src="@/assets/styles/reset-password.css"></style>
