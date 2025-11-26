<!-- Illustration hero pour les pages d'authentification (vue gauche du layout). -->
<!-- ===== Bloc illustration onboarding ===== -->
<template>
  <section class="auth-illustration">
    <!-- Overlay translucide + contenu superpose pour garder la photo lisible -->
    <div class="auth-illustration__overlay"></div>
    <div class="auth-illustration__content">
      <!-- Badge de confiance affiche en haut de l'illustration -->
      <div class="auth-badge">
        <i class="bi bi-stars me-2"></i>
        Onboarding maîtrisé
      </div>
      <h1>
        Lancez votre espace collaboratif
        <span class="brand-text">COVA</span>
      </h1>
      <p>
        Déployez en toute simplicité un environnement souverain pour vos équipes.
        Nous accompagnons chaque organisation vers un démarrage sécurisé et fluide.
      </p>
      <!-- Liste courte des benefices mis en avant pendant l'authentification -->
      <ul class="auth-feature-list">
        <li>
          <span class="feature-icon"><i class="bi bi-person-badge-fill"></i></span>
          Validation des identités et contrôle des accès à la volée.
        </li>
        <li>
          <span class="feature-icon"><i class="bi bi-diagram-3-fill"></i></span>
          Espaces partagés, canaux projets et archivage automatique.
        </li>
        <li>
          <span class="feature-icon"><i class="bi bi-headset"></i></span>
          Experts COVA dédiés pour configurer vos règles de sécurité.
        </li>
      </ul>
      <!-- Indicateurs chiffres pour rassurer sur la rapidite et la disponibilite -->
      <div class="auth-metrics">
        <div>
          <strong>&lt; 5 min</strong>
          <span>pour activer votre équipe</span>
        </div>
        <div>
          <strong>99,9%</strong>
          <span>disponibilité garantie</span>
        </div>
      </div>
    </div>
  </section>
</template>

<!-- ===== Styles specifique a l'illustration ===== -->
<style scoped>
/* Bloc hero avec dégradé et badges pour rassurer l'utilisateur. */
.auth-illustration {
  /* Layout principal du panneau illustration */
  position: relative;
  border-radius: 36px;
  overflow: hidden;
  background: linear-gradient(140deg, #183c87 0%, #1959c2 45%, #5ad3f5 100%);
  color: #fff;
  display: flex;
  align-items: flex-end;
  padding: clamp(2.5rem, 3vw, 3.5rem);
  box-shadow: 0 24px 60px rgba(20, 64, 140, 0.35);
}

/* ===== Sous-elements et badges ===== */
.auth-illustration__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.18) 0%, rgba(9, 21, 58, 0.35) 100%);
  mix-blend-mode: screen;
  opacity: 0.75;
}

.auth-illustration__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 1.35rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-weight: 600;
  font-size: 0.95rem;
  text-transform: uppercase;
}

.auth-feature-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.auth-feature-list li {
  display: flex;
  gap: 0.9rem;
}

.feature-icon {
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  display: grid;
  place-items: center;
}

.auth-metrics {
  display: flex;
  gap: 2.5rem;
}
</style>
