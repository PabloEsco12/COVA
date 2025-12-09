<!--
  ===== Component Footer =====
  Component: DashboardFooter
  Role: Bandeau de bas de page avec informations légales et support.
-->
<template>
  <footer class="dashboard-footer" :class="{ 'dashboard-footer-dark': isDark }">
    <div class="footer-top">
      <div class="footer-brand">
        <div class="logo-badge">C</div>
        <div>
          <p class="brand-title mb-1">COVA Messagerie</p>
          <p class="brand-subtitle mb-0 text-muted">
            Confidentialité, traçabilité, conformité RGPD.
          </p>
        </div>
      </div>

      <div class="footer-columns">
        <div class="footer-column">
          <p class="footer-heading">Confiance</p>
          <a class="footer-link" href="#">Politique de confidentialité</a>
          <a class="footer-link" href="#">Conditions d'utilisation</a>
          <a class="footer-link" href="#">Mentions légales</a>
        </div>

        <div class="footer-column">
          <p class="footer-heading">Sécurité</p>
          <a class="footer-link" href="#">Plan de continuité</a>
          <a class="footer-link" href="#">Journal d'audit</a>
          <RouterLink class="footer-link" to="/dashboard/settings">
            Paramètres &amp; sécurité
          </RouterLink>
        </div>

        <div class="footer-column">
          <p class="footer-heading">Support</p>
          <RouterLink class="footer-link" to="/dashboard/faq">
            FAQ &amp; Centre d'aide
          </RouterLink>
          <a class="footer-link" href="mailto:support@covamessagerie.be">
            support@covamessagerie.be
          </a>
          <a class="footer-link" href="tel:+32102030405">+32 1 02 03 04 05</a>
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <div class="d-flex align-items-center gap-2">
        <span class="status-dot"></span>
        <span class="small text-muted">
          Chiffrement de bout en bout actif — SLA 99.9%
        </span>
      </div>
      <div class="footer-legal">
        <span class="small text-muted">© {{ currentYear }} COVA Messagerie</span>
        <div class="legal-links">
          <a class="footer-link small" href="#">Politique de cookies</a>
          <RouterLink class="footer-link small" to="/dashboard/faq">
            Centre de confiance
          </RouterLink>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  isDark: { type: Boolean, default: false },
})

const currentYear = new Date().getFullYear()
</script>

<style scoped>
.dashboard-footer {
  margin-top: 1rem;
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, #f9fbff 0%, #eef2f8 100%);
  border-radius: 18px;
  border: 1px solid #e4e9f5;
  box-shadow: 0 10px 28px rgba(25, 89, 194, 0.12);
}

.dashboard-footer-dark {
  background: linear-gradient(135deg, #121722 0%, #0f131c 100%);
  border: 1px solid #1e2533;
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.6);
}

.footer-top {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
}

@media (min-width: 992px) {
  .footer-top {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-badge {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0d6efd 0%, #3a7bd5 100%);
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 8px 22px rgba(13, 110, 253, 0.45);
}

.dashboard-footer-dark .logo-badge {
  background: linear-gradient(135deg, #1e63ff 0%, #1d9bf0 100%);
  color: #f2f5ff;
  box-shadow: 0 8px 22px rgba(29, 155, 240, 0.35);
}

.brand-title {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.brand-subtitle {
  font-size: 0.85rem;
}

.footer-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem 1.5rem;
  width: 100%;
}

@media (min-width: 992px) {
  .footer-columns {
    width: auto;
    min-width: 480px;
  }
}

.footer-column {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.footer-heading {
  margin: 0;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6c7a96;
  font-weight: 700;
}

.dashboard-footer-dark .footer-heading {
  color: #8ea3c5;
}

.footer-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: #2450a5;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
}

.footer-link:hover {
  color: #0d6efd;
  text-decoration: underline;
}

.dashboard-footer-dark .footer-link {
  color: #d3defa;
}

.dashboard-footer-dark .footer-link:hover {
  color: #f5f8ff;
}

.footer-bottom {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 1rem;
  margin-top: 1rem;
  border-top: 1px solid rgba(13, 110, 253, 0.12);
}

.dashboard-footer-dark .footer-bottom {
  border-top-color: rgba(255, 255, 255, 0.08);
}

.footer-legal {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  align-items: flex-start;
}

@media (min-width: 768px) {
  .footer-bottom {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .footer-legal {
    align-items: flex-end;
  }
}

.legal-links {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: #28a745;
  box-shadow: 0 0 0 8px rgba(40, 167, 69, 0.12);
}

.dashboard-footer-dark .status-dot {
  background: #2ddf9d;
  box-shadow: 0 0 0 8px rgba(45, 223, 157, 0.1);
}
</style>
