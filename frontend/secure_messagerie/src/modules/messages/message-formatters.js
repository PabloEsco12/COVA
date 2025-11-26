// ===== Module Header =====
// Module: messages/message-formatters
// Role: Assemble des helpers de presentation lies aux messages (statuts, securite, formats).
// Usage: expose des fonctions derivees (labels/classes/tooltips) basees sur les props message existantes.
// Notes: functions pures, aucune dependance DOM; relies sur extractDeliverySummary et formateurs externes.

export function createMessageFormatters({
  formatTime,
  formatAbsolute,
  formatFileSize,
  extractDeliverySummary,
}) {
  // ---- Libelle humain du statut (priorise le point de vue "moi" vs autres) ----
  function messageStatusLabel(message) {
    if (message.sentByMe) {
      const summary = extractDeliverySummary(message)
      if (summary.total <= 0) return 'Envoyé'
      if (summary.read >= summary.total) return 'Lu'
      if (summary.delivered > 0) return 'Distribué'
      return 'En cours'
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

  // ---- Classe CSS pour styliser le statut visuel (pastille) ----
  function messageStatusClass(message) {
    if (message.sentByMe) {
      const summary = extractDeliverySummary(message)
      if (summary.total > 0 && summary.read >= summary.total) return 'state-read'
      if (summary.delivered > 0) return 'state-delivered'
      return 'state-queued'
    }
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

  // ---- Detail additionnel (horodatage de lecture/livraison ou suppression) ----
  function messageStatusDetail(message) {
    if (message.deleted) return 'Supprimé'
    if (message.sentByMe) return ''
    if (message.readAt) return `Lu ${formatTime(message.readAt)}`
    if (message.deliveredAt) return `Distribué ${formatTime(message.deliveredAt)}`
    return ''
  }

  // ---- Etiquette courte du schema de securite ----
  function messageSecurityLabel(message) {
    const scheme = message.security?.scheme || 'confidentiel'
    if (scheme === 'plaintext') return 'Chiffrage applicatif'
    return `Schéma ${scheme}`
  }

  // ---- Tooltip detaille: schema + metadonnees ----
  function messageSecurityTooltip(message) {
    const metadata = message.security?.metadata || {}
    const lines = Object.entries(metadata).map(([key, value]) => `${key}: ${value}`)
    return [`Schéma: ${message.security?.scheme || 'n/a'}`, ...lines].join('\n')
  }

  return {
    formatTime,
    formatAbsolute,
    formatFileSize,
    messageStatusLabel,
    messageStatusClass,
    messageStatusDetail,
    messageSecurityLabel,
    messageSecurityTooltip,
  }
}
