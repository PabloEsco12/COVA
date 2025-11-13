// src/composables/useTyping.js
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRealtime } from './useRealtime'

/**
 * Gère l’état “en train d’écrire” pour une conversation.
 *
 * @param {string|number|null} conversationId
 * @param {number|string} myUserId
 * @param {Object} [options]
 * @param {Function} [options.onTypingUsersChanged] - callback(Array<userId>)
 * @param {Object}   [options.realtime]             - instance retournée par useRealtime (facultatif)
 *     -> si fournie, on NE crée PAS une 2e WebSocket: on s’appuie dessus (send / updateConversation).
 *
 * Retourne:
 *  - connect / disconnect (si on gère un WS local)
 *  - sendTypingStart / sendTypingStop
 *  - typingUsers (Set-like en Array)
 *  - isTyping (boolean)
 */
export function useTyping(conversationId, myUserId, options = {}) {
  const { onTypingUsersChanged, realtime: externalRealtime } = options

  // Map userId -> last timestamp (ms)
  const typingMap = ref(new Map())
  const TYPING_TIMEOUT = 5000  // expire après 5s
  const CLEANUP_EVERY = 1000   // vérif 1x/s

  // Si un realtime externe est passé, on l’utilise. Sinon on en crée un, avec uniquement le handler typing.
  const localRealtime = !externalRealtime
    ? useRealtime(conversationId, { onTyping: handleTypingEvent })
    : null

  const rt = externalRealtime || localRealtime

  // Interval de cleanup
  let cleanupTimer = null
  // Débounce local pour limiter l’envoi de typing:start
  let typingStartTimer = null

  function handleTypingEvent(evt) {
    const { event, payload } = evt || {}
    const userId = payload?.user_id
    // Ignore: pas d’ID ou moi-même
    if (!userId || String(userId) === String(myUserId)) return

    if (event === 'typing:start') {
      typingMap.value.set(String(userId), Date.now())
    } else if (event === 'typing:stop') {
      typingMap.value.delete(String(userId))
    }
    cleanup()
    onTypingUsersChanged?.(Array.from(typingMap.value.keys()))
  }

  function cleanup() {
    const now = Date.now()
    let changed = false
    for (const [id, ts] of typingMap.value.entries()) {
      if (now - ts > TYPING_TIMEOUT) {
        typingMap.value.delete(id)
        changed = true
      }
    }
    if (changed) {
      onTypingUsersChanged?.(Array.from(typingMap.value.keys()))
    }
  }

  function startCleanupLoop() {
    stopCleanupLoop()
    cleanupTimer = setInterval(cleanup, CLEANUP_EVERY)
  }
  function stopCleanupLoop() {
    if (cleanupTimer) {
      clearInterval(cleanupTimer)
      cleanupTimer = null
    }
  }

  // API d’envoi
  function sendTypingStart() {
    // Débounce pour éviter d’inonder le backend si l’utilisateur tape vite.
    if (typingStartTimer) clearTimeout(typingStartTimer)
    typingStartTimer = setTimeout(() => {
      rt.send('typing:start', {
        conversation_id: conversationId ?? null,
        user_id: myUserId,
      })
    }, 150) // petit délai pour agréger les frappes
  }

  function sendTypingStop() {
    if (typingStartTimer) {
      clearTimeout(typingStartTimer)
      typingStartTimer = null
    }
    rt.send('typing:stop', {
      conversation_id: conversationId ?? null,
      user_id: myUserId,
    })
  }

  // Reset quand la conversation change
  watch(
    () => conversationId,
    (next, prev) => {
      if (String(next) === String(prev)) return
      typingMap.value.clear()
      onTypingUsersChanged?.([])
      // Si on gère une socket locale, on met à jour la conv (reconnexion automatique)
      if (localRealtime) {
        localRealtime.updateConversation(next ?? null)
      }
    },
    { immediate: false },
  )

  // Lifecycle
  onMounted(() => {
    startCleanupLoop()
    if (localRealtime) {
      // Si on a créé un WS local, on connecte maintenant.
      localRealtime.connect()
    } else {
      // Si on a un realtime externe, on doit brancher son handler typing.
      // Deux options :
      //  1) Le parent a passé un handler onTyping dans useRealtime (recommandé)
      //  2) Sinon, on peut écouter depuis ailleurs ; ici on se contente d’utiliser rt.send().
      // Dans ce composable, on part du principe que le parent a déjà connecté le realtime
      // et branché onTyping vers handleTypingEvent si nécessaire.
    }
  })

  onBeforeUnmount(() => {
    stopCleanupLoop()
    if (localRealtime) {
      localRealtime.disconnect()
    }
    if (typingStartTimer) {
      clearTimeout(typingStartTimer)
      typingStartTimer = null
    }
  })

  // Expose lisible: tableau d’IDs
  const typingUsers = computed(() => Array.from(typingMap.value.keys()))
  const isTyping = computed(() => typingMap.value.size > 0)

  return {
    // Connexion uniquement si on gère un WS local
    connect: localRealtime?.connect,
    disconnect: localRealtime?.disconnect,

    sendTypingStart,
    sendTypingStop,

    typingUsers,
    isTyping,
  }
}
