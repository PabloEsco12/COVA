// ===== Module Header =====
// Module: messages/formatters
// Author: Valentin Masurelle
// Date: 2025-11-26
// Role: Helpers pour formatter statuts/labels lies aux messages et contenus enrichis (gif/strip links).
// Usage:
//  - Fonctions pures importees dans les composables et composants pour un affichage coherent.
//  - Centralise l'usage de detectGifLinks/stripGifLinks pour eviter la duplication de logique UI.
//  - Rassemble tous les formateurs (horodatage, tailles, apercus) pour garder un rendu stable.
//  - Aucun acces DOM : les helpers sont testables en unitaires et peuvent etre reutilises cote serveur.

import { detectGifLinks, stripGifLinks } from '@/utils/messageContent'

// ---- Horodatage court (HH:MM) pour bulles/messages envoyes ----
export function formatTime(date) {
  if (!(date instanceof Date)) return ''
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

// ---- Horodatage court pour les listes (accepte Date ou timestamp) ----
export function formatListTime(date) {
  const value = date instanceof Date ? date : new Date(date || Date.now())
  return value.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

// ---- Date absolue (dateStyle + timeStyle) pour les infobulles ou historiques ----
export function formatAbsolute(date) {
  if (!(date instanceof Date)) return ''
  return date.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
}

// ---- Humanisation des tailles d'attachement (Ko/Mo/Go) ----
export function formatFileSize(bytes) {
  if (typeof bytes !== 'number' || Number.isNaN(bytes)) return ''
  if (bytes < 1024) return `${bytes} o`
  const units = ['Ko', 'Mo', 'Go', 'To']
  let size = bytes / 1024
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unit]}`
}

// ---- Apercu de message: extrait textuel ou fallback (GIF, PJ, contenu brut) ----
export function messagePreviewText(message) {
  if (!message) return ''
  if (message.excerpt) return message.excerpt
  if (message.content) {
    const gifs = detectGifLinks(message.content)
    const trimmed = stripGifLinks(message.content, gifs).trim()
    if (gifs.length && !trimmed) {
      return 'GIF partagé'
    }
    return trimmed || String(message.content).slice(0, 120)
  }
  if (Array.isArray(message.attachments) && message.attachments.length) {
    return `${message.attachments.length} piece(s) jointe(s)`
  }
  if (typeof message.attachments === 'number' && message.attachments > 0) {
    return `${message.attachments} piece(s) jointe(s)`
  }
  return ''
}

// ---- Normalisation robuste du resume d'acheminement (totaux/delivre/lu) ----
export function extractDeliverySummary(message) {
  const summary = message.deliverySummary || {}
  return {
    total: Number(summary.total || 0),
    delivered: Number(summary.delivered || 0),
    read: Number(summary.read || 0),
    pending: Number(summary.pending || 0),
  }
}
