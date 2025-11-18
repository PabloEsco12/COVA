<template>
  <div class="faq-page">
    <header class="faq-hero">
      <p class="eyebrow">Centre d'aide</p>
      <h1>Questions fréquentes</h1>
      <p class="subtitle">
        Retrouvez les réponses aux demandes les plus courantes sur COVA. Pour toute
        assistance urgente, utilisez les options de contact en bas de page.
      </p>
    </header>

    <section class="faq-content">
      <article
        v-for="section in faqSections"
        :key="section.title"
        class="faq-section"
      >
        <div class="section-header">
          <i :class="section.icon" aria-hidden="true"></i>
          <div>
            <h2>{{ section.title }}</h2>
            <p>{{ section.description }}</p>
          </div>
        </div>
        <div class="qa-grid">
          <details
            v-for="item in section.items"
            :key="item.question"
            class="faq-item"
          >
            <summary>
              {{ item.question }}
            </summary>
            <p v-for="(paragraph, index) in item.answer" :key="index">
              {{ paragraph }}
            </p>
            <ul v-if="item.list">
              <li v-for="line in item.list" :key="line">
                {{ line }}
              </li>
            </ul>
          </details>
        </div>
      </article>
    </section>

    <section class="faq-help">
      <div>
        <h3>Besoin d'une assistance personnalisée ?</h3>
        <p>
          Notre équipe support répond sous 4 heures ouvrées. Préparez idéalement une capture
          d'écran et l'heure approximative du problème.
        </p>
      </div>
      <div class="contact-actions">
        <a class="btn btn-primary" href="mailto:support@covamessageries.be">
          <i class="bi bi-envelope-fill me-2"></i>
          support@covamessageries.be
        </a>
        <p class="contact-hint">
          Privilégiez le mail sécurisé pour l’instant. Les canaux chat et téléphone seront annoncés
          dès leur mise en service.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
const faqSections = [
  {
    title: 'Compte & sécurité',
    description: 'Gestion du profil, authentification multifacteur et confidentialité.',
    icon: 'bi bi-shield-lock-fill',
    items: [
      {
        question: 'Comment activer la validation en deux étapes (MFA) ?',
        answer: [
          'Rendez-vous dans Paramètres > Sécurité, cliquez sur « Activer MFA » puis scannez le QR code avec votre application d’authentification.',
          'Saisissez le code généré pour finaliser l’activation. Lors de vos prochaines connexions, ce code vous sera demandé après le mot de passe.',
        ],
      },
      {
        question: 'Que faire en cas de mot de passe oublié ?',
        answer: [
          'Depuis la page de connexion, cliquez sur « Mot de passe oublié ». Saisissez votre adresse professionnelle : un lien sécurisé vous sera envoyé.',
          'Si vous n’avez plus accès à votre messagerie, contactez immédiatement votre administrateur interne.',
        ],
      },
      {
        question: 'Comment modifier la visibilité de mon profil ?',
        answer: [
          'Dans Paramètres > Confidentialité, ajustez la visibilité du pseudo, de l’avatar ou des coordonnées. Les changements sont instantanés.',
        ],
      },
    ],
  },
  {
    title: 'Conversations & fichiers',
    description: 'Envoi de messages, invitations et partage de documents.',
    icon: 'bi bi-chat-square-heart-fill',
    items: [
      {
        question: 'Quels formats de pièces jointes sont autorisés ?',
        answer: [
          'Les documents PDF, DOCX, XLSX, images (PNG/JPG/GIF), archives ZIP et fichiers texte sont pris en charge jusqu’à 25 Mo par fichier.',
        ],
      },
      {
        question: 'Comment inviter un nouveau contact ?',
        answer: [
          'Cliquez sur « Inviter un contact » dans la barre latérale, saisissez son adresse email professionnelle puis validez.',
        ],
        list: [
          'L’invitation reste valable 7 jours.',
          'Vous pouvez relancer ou révoquer l’invitation depuis l’onglet Contacts > Demandes en attente.',
        ],
      },
      {
        question: 'Puis-je éditer ou supprimer un message envoyé ?',
        answer: [
          'Oui, survolez le message et utilisez le menu « … » pour l’éditer ou le supprimer, dans la limite des règles définies par votre organisation.',
        ],
      },
    ],
  },
  {
    title: 'Notifications & appareils',
    description: 'Suivi des alertes, gestion des sessions et bonnes pratiques.',
    icon: 'bi bi-bell-fill',
    items: [
      {
        question: 'Je ne reçois plus les notifications navigateur, que faire ?',
        answer: [
          'Vérifiez que les notifications sont autorisées pour covamessageries.be dans votre navigateur (icône cadenas à gauche de l’URL).',
          'Dans la barre latérale COVA, assurez-vous que l’interrupteur Notifications est activé.',
        ],
      },
      {
        question: 'Comment gérer mes appareils connectés ?',
        answer: [
          'Rendez-vous dans l’onglet Appareils pour consulter les sessions actives. Cliquez sur « Révoquer » pour déconnecter un appareil que vous ne reconnaissez pas.',
        ],
      },
      {
        question: 'Le lien de téléchargement d’une pièce jointe ne fonctionne plus.',
        answer: [
          'Pour des raisons de sécurité, les liens expirent au bout de quelques minutes. Rouvrez la conversation et relancez le téléchargement.',
        ],
      },
    ],
  },
]

</script>

<style scoped>
.faq-page {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.faq-hero {
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.15), rgba(99, 102, 241, 0.18));
  border-radius: 20px;
  padding: 1.75rem;
  color: #0f172a;
  box-shadow: 0 15px 30px rgba(15, 23, 42, 0.15);
}

.main-content-dark .faq-hero {
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.25), rgba(99, 102, 241, 0.28));
  color: #e2e8f0;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}

.faq-hero h1 {
  font-size: 2.2rem;
  margin-bottom: 0.35rem;
}

.faq-hero .subtitle {
  max-width: 640px;
  margin: 0;
  color: inherit;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 0.8rem;
  margin-bottom: 0.8rem;
  color: rgba(15, 23, 42, 0.65);
}

.main-content-dark .eyebrow {
  color: rgba(226, 232, 240, 0.7);
}

.faq-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.faq-section {
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
  padding: 1.5rem;
}

.main-content-dark .faq-section {
  background: rgba(21, 26, 35, 0.9);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
  color: #e2e8f0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.section-header i {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: rgba(13, 110, 253, 0.15);
  color: #0d6efd;
}

.main-content-dark .section-header i {
  background: rgba(13, 110, 253, 0.25);
  color: #93c5fd;
}

.section-header h2 {
  margin: 0;
  font-size: 1.4rem;
}

.qa-grid {
  display: grid;
  gap: 1rem;
}

.faq-item {
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 0.9rem 1rem;
  background: rgba(245, 247, 255, 0.8);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.faq-item summary {
  font-weight: 600;
  cursor: pointer;
  list-style: none;
}

.faq-item summary::-webkit-details-marker {
  display: none;
}

.faq-item summary::after {
  content: '›';
  float: right;
  transform: rotate(90deg);
  transition: transform 0.2s ease;
}

.faq-item[open] summary::after {
  transform: rotate(-90deg);
}

.faq-item p {
  margin: 0.75rem 0 0;
  color: rgba(15, 23, 42, 0.85);
}

.faq-item ul {
  margin: 0.5rem 0 0 1.2rem;
  padding: 0;
  color: rgba(15, 23, 42, 0.85);
}

.main-content-dark .faq-item {
  background: rgba(30, 34, 45, 0.85);
  border-color: rgba(147, 197, 253, 0.2);
}

.main-content-dark .faq-item p,
.main-content-dark .faq-item ul {
  color: rgba(226, 232, 240, 0.9);
}

.faq-help {
  border-radius: 20px;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.18), rgba(14, 165, 233, 0.2));
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 16px 32px rgba(13, 110, 253, 0.2);
}

.main-content-dark .faq-help {
  background: linear-gradient(135deg, rgba(15, 118, 243, 0.3), rgba(17, 94, 236, 0.35));
}

.contact-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.contact-hint {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
}
</style>
