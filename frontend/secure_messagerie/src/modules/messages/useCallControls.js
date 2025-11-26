// ===== Module Header =====
// Module: messages/useCallControls
// Role: Piloter les appels WebRTC (audio/video): etat local, signaux, peer connection, toggles UI.
// Notes:
//  - State centralise (callState/callControls) pour le panneau d'appel et les boutons.
//  - Ne gere pas l'UI, seulement les flux et les signaux envoyes via sendCallSignal.
//  - Requiert l'injection des callbacks reseau (ensurePeerConnectionReady, attachStream, notifyIncomingSummary).
import { computed, reactive, ref, watch } from 'vue'

export function useCallControls({
  selectedConversation,
  selectedConversationId,
  currentUserId,
  displayNameForUser,
  sendCallSignal,
  notifyIncomingSummary,
  addLocalCallLog,
  ensurePeerConnectionReady,
  attachStream,
  generateCallId,
}) {
  const localVideoRef = ref(null)
  const remoteAudioRef = ref(null)
  const remoteVideoRef = ref(null)
  // ---- Etat principal de l'appel (phase, ids, flux locaux/distants) ----
  const callState = reactive({
    status: 'idle',
    callId: null,
    kind: 'audio',
    remoteUserId: null,
    incomingOffer: null,
    initiator: false,
    error: '',
    localStream: null,
    remoteStream: null,
  })
  // ---- Etat des controles UI (micro/camera) ----
  const callControls = reactive({
    micEnabled: true,
    cameraEnabled: true,
  })
  // ---- File d'attente des ICE recues avant creation du peer ----
  const pendingIceCandidates = []
  let peerConnection = null
  // ---- Configuration STUN par defaut (no TURN pour simplifier la demo) ----
  const rtcConfig = {
    iceServers: [{ urls: ['stun:stun.l.google.com:19302', 'stun:stun1.l.google.com:19302'] }],
  }

  // ---- Libelles derives pour l'UI ----
  const remoteDisplayName = computed(() => {
    if (callState.remoteUserId) {
      return displayNameForUser(callState.remoteUserId)
    }
    return 'Participant'
  })

  // Affichage du statut courant de l'appel (header composant)
  const callStatusLabel = computed(() => {
    switch (callState.status) {
      case 'incoming':
        return `${remoteDisplayName.value} vous appelle`
      case 'outgoing':
        return `Connexion avec ${remoteDisplayName.value}`
      case 'connecting':
        return `Initialisation de l'appel`
      case 'connected':
        return `En communication avec ${remoteDisplayName.value}`
      default:
        return 'Appel sécurisé'
    }
  })

  // ---- Logging securise (evite crash console) ----
  function callLog(...args) {
    try {
      console.info('[call]', ...args)
    } catch {
      /* ignore */
    }
  }

  // ---- Stoppe proprement les tracks d'un MediaStream ----
  function stopStream(stream) {
    if (!stream) return
    stream.getTracks().forEach((track) => {
      try {
        track.stop()
      } catch {
        /* ignore */
      }
    })
  }

  // ---- Centralise la mise a jour des erreurs visuelles ----
  function setCallError(err) {
    if (!err) {
      callState.error = ''
      return
    }
    if (typeof err === 'string') {
      callState.error = err
    } else {
      callState.error = err.message || "La connexion à l'appel a échoué."
    }
    callLog('call error', callState.error)
  }

  // ---- Stoppe et nettoie le generateur sonore (incoming/outgoing) ----
  function stopRingtone(handles) {
    const { intervalRef, oscillatorRef, gainRef } = handles
    try {
      if (intervalRef.value) {
        clearInterval(intervalRef.value)
      }
      if (oscillatorRef.value) {
        oscillatorRef.value.stop()
        oscillatorRef.value.disconnect()
      }
      if (gainRef.value) {
        gainRef.value.disconnect()
      }
    } catch {
      /* ignore */
    }
    intervalRef.value = null
    oscillatorRef.value = null
    gainRef.value = null
  }

  // ---- Genere une sonnerie "maison" pour incoming/outgoing ----
  function startRingtone(handles, mode = 'outgoing') {
    const { contextRef, intervalRef, oscillatorRef, gainRef } = handles
    try {
      if (!contextRef.value) {
        const Ctx = window.AudioContext || window.webkitAudioContext
        if (!Ctx) return
        contextRef.value = new Ctx()
      }
      stopRingtone(handles)
      const seq = mode === 'incoming' ? [523, 659, 784, 659] : [494, 622, 740, 622]
      oscillatorRef.value = contextRef.value.createOscillator()
      gainRef.value = contextRef.value.createGain()
      oscillatorRef.value.type = 'sine'
      oscillatorRef.value.frequency.value = seq[0]
      gainRef.value.gain.value = 0.02
      oscillatorRef.value.connect(gainRef.value)
      gainRef.value.connect(contextRef.value.destination)
      contextRef.value.resume?.()
      oscillatorRef.value.start()
      let idx = 0
      intervalRef.value = setInterval(() => {
        if (!oscillatorRef.value) {
          clearInterval(intervalRef.value)
          intervalRef.value = null
          return
        }
        idx = (idx + 1) % seq.length
        oscillatorRef.value.frequency.value = seq[idx]
      }, 480)
    } catch (err) {
      callLog('ringtone error', err?.message || err)
    }
  }

  const ringtoneHandles = {
    contextRef: ref(null),
    oscillatorRef: ref(null),
    gainRef: ref(null),
    intervalRef: ref(null),
  }

  // ---- Creation/renouvellement du RTCPeerConnection et wiring des handlers ----
  async function createPeerConnection(stream) {
    if (peerConnection) {
      try {
        peerConnection.close()
      } catch {
        /* ignore */
      }
      peerConnection = null
    }
    peerConnection = new RTCPeerConnection(rtcConfig)
    peerConnection.ontrack = (event) => {
      const [remote] = event.streams
      callLog('ontrack', event.track?.kind, {
        streams: event.streams?.length,
        trackMuted: event.track?.muted,
      })
      if (event.track) {
        event.track.onmute = () => callLog('track muted', event.track.kind)
        event.track.onunmute = () => callLog('track unmuted', event.track.kind)
        event.track.onended = () => callLog('track ended', event.track.kind)
      }
      if (remote) {
        callState.remoteStream = remote
      }
    }
    peerConnection.onicecandidate = (event) => {
      if (event.candidate && callState.callId && callState.remoteUserId) {
        sendCallSignal('call:candidate', {
          call_id: callState.callId,
          target_user_id: callState.remoteUserId,
          candidate: {
            candidate: event.candidate.candidate,
            sdpMid: event.candidate.sdpMid,
            sdpMLineIndex: event.candidate.sdpMLineIndex,
          },
        })
      }
    }
    peerConnection.oniceconnectionstatechange = () => {
      if (peerConnection) {
        callLog('ice state', peerConnection.iceConnectionState)
      }
    }
    peerConnection.onconnectionstatechange = () => {
      if (!peerConnection) return
      if (peerConnection.connectionState === 'connected') {
        callLog('peer connection connected')
        callState.status = 'connected'
      } else if (peerConnection.connectionState === 'failed') {
        callLog('peer connection failed')
        setCallError('La connexion a échoué.')
        endCall(true)
      }
      if (['connected', 'failed', 'disconnected', 'closed'].includes(peerConnection.connectionState)) {
        stopRingtone(ringtoneHandles)
      }
    }
    if (stream) {
      stream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, stream)
      })
    }
  }

  function serializeDescription(desc) {
    if (!desc) return null
    return { type: desc.type, sdp: desc.sdp }
  }

  // ---- Demande d'acces audio/video (avec contraintes anti-bruit) ----
  async function requestMedia(kind = 'audio') {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      throw new Error('Votre navigateur ne permet pas les appels sécurisés.')
    }
    const constraints = {
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: kind === 'video',
    }
    return navigator.mediaDevices.getUserMedia(constraints)
  }

  // ---- Trouve l'interlocuteur par defaut (autre membre actif de la conversation) ----
  function getDefaultCallTarget() {
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.members)) return null
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    return (
      conv.members.find(
        (member) => member.state === 'active' && (!selfId || member.userId !== selfId),
      ) || null
    )
  }

  // ---- Initie un appel sortant (genere offre + sonnerie) ----
  async function startCall(kind = 'audio') {
    callLog('startCall requested', kind)
    callState.error = ''
    if (!selectedConversationId.value) {
      setCallError('Aucune conversation active.')
      return
    }
    if (callState.status !== 'idle') {
      setCallError('Un autre appel est déjà en cours.')
      return
    }
    const target = getDefaultCallTarget()
    if (!target) {
      setCallError('Aucun interlocuteur disponible dans cette conversation.')
      return
    }
    callState.kind = kind
    callState.remoteUserId = target.id
    callState.callId = generateCallId()
    callState.initiator = true
    callState.status = 'connecting'
    callState.error = ''
    callControls.micEnabled = true
    callControls.cameraEnabled = kind === 'video'
    try {
      const stream = await requestMedia(kind)
      stream.getAudioTracks().forEach((track) => {
        track.enabled = callControls.micEnabled
      })
      stream.getVideoTracks().forEach((track) => {
        track.enabled = callControls.cameraEnabled
      })
      callState.localStream = stream
      await createPeerConnection(stream)
      const offer = await peerConnection.createOffer()
      await peerConnection.setLocalDescription(offer)
      callState.status = 'outgoing'
      startRingtone(ringtoneHandles, 'outgoing')
      const description = serializeDescription(peerConnection.localDescription)
      if (!description) throw new Error("Impossible de préparer l'offre.")
      sendCallSignal('call:offer', {
        call_id: callState.callId,
        target_user_id: callState.remoteUserId,
        kind,
        sdp: description,
      })
    } catch (err) {
      callLog('startCall error', err?.message || err)
      setCallError(err)
      endCall(true)
    }
  }

  // ---- Accepte un appel entrant (offre -> reponse, fallback audio si video refuse) ----
  async function acceptIncomingCall() {
    const offer = callState.incomingOffer
    if (!offer) return
    callLog('acceptIncomingCall', offer.call_id || callState.callId || 'no-call-id')
    stopRingtone(ringtoneHandles)
    callState.error = ''
    callState.status = 'connecting'
    callControls.micEnabled = true
    callControls.cameraEnabled = callState.kind === 'video'
    const attemptKinds = callState.kind === 'video' ? ['video', 'audio'] : ['audio']
    for (const attempt of attemptKinds) {
      try {
        callState.kind = attempt
        callControls.cameraEnabled = attempt === 'video'
        const stream = await requestMedia(attempt)
        stream.getAudioTracks().forEach((track) => {
          track.enabled = callControls.micEnabled
        })
        stream.getVideoTracks().forEach((track) => {
          track.enabled = callControls.cameraEnabled
        })
        callState.localStream = stream
        await createPeerConnection(stream)
        if (offer.sdp) {
          await peerConnection.setRemoteDescription(offer.sdp)
        }
        const answer = await peerConnection.createAnswer()
        await peerConnection.setLocalDescription(answer)
        flushPendingCandidates()
        const description = serializeDescription(peerConnection.localDescription)
        if (!description) throw new Error("Impossible de préparer la réponse.")
        sendCallSignal('call:answer', {
          call_id: callState.callId,
          target_user_id: callState.remoteUserId,
          kind: callState.kind,
          sdp: description,
        })
        callState.incomingOffer = null
        return
      } catch (err) {
        callLog('acceptIncomingCall error', attempt, err?.message || err)
        if (attempt === 'audio') {
          setCallError(err)
          endCall(true)
          return
        }
      }
    }
  }

  // ---- Termine l'appel et nettoie les flux/handlers (optionnellement notifie le pair) ----
  function endCall(silent = false, options = {}) {
    callLog('endCall', { silent, options, callId: callState.callId })
    stopRingtone(ringtoneHandles)
    const currentCallId = callState.callId
    const remoteId = callState.remoteUserId
    const callSummary = {
      callId: currentCallId,
      kind: callState.kind,
      initiator: callState.initiator,
      remote: remoteDisplayName.value,
      reason: options.reason || 'ended',
    }
    if (peerConnection) {
      try {
        peerConnection.ontrack = null
        peerConnection.onicecandidate = null
        peerConnection.close()
      } catch {
        /* ignore */
      }
      peerConnection = null
    }
    stopStream(callState.localStream)
    stopStream(callState.remoteStream)
    callState.localStream = null
    callState.remoteStream = null
    callState.incomingOffer = null
    callState.status = 'idle'
    callState.kind = 'audio'
    callState.callId = null
    callState.remoteUserId = null
    callState.initiator = false
    callState.error = ''
    callControls.micEnabled = true
    callControls.cameraEnabled = true
    pendingIceCandidates.length = 0
    if (callSummary.callId && selectedConversationId.value) {
      addLocalCallLog(callSummary)
    }
    if (!silent && currentCallId && remoteId) {
      sendCallSignal('call:hangup', {
        call_id: currentCallId,
        target_user_id: remoteId,
        reason: options.reason || 'hangup',
      })
    }
  }

  // ---- Ajoute les ICE candidates recues avant l'init du peer ----
  function flushPendingCandidates() {
    if (!peerConnection || !pendingIceCandidates.length) return
    while (pendingIceCandidates.length) {
      const candidate = pendingIceCandidates.shift()
      if (!candidate) continue
      try {
        peerConnection.addIceCandidate(candidate)
      } catch {
        /* ignore */
      }
    }
  }

  // ---- Reception d'une offre entrante (prepare l'appel entrant) ----
  function handleIncomingOffer(data) {
    const fromUserId = data.from_user_id ? String(data.from_user_id) : null
    if (callState.status !== 'idle') {
      callLog('incoming offer while busy', data.call_id, 'current', callState.callId)
      if (data.call_id && fromUserId) {
        sendCallSignal('call:hangup', {
          call_id: data.call_id,
          target_user_id: fromUserId,
          reason: 'busy',
        })
      }
      return
    }
    callState.callId = data.call_id || generateCallId()
    callState.kind = data.kind || 'audio'
    callState.remoteUserId = fromUserId
    callState.incomingOffer = data
    callState.status = 'incoming'
    callState.error = ''
    callControls.micEnabled = true
    callControls.cameraEnabled = callState.kind === 'video'
    startRingtone(ringtoneHandles, 'incoming')
    callLog('incoming call', {
      callId: callState.callId,
      kind: callState.kind,
      from: callState.remoteUserId,
    })
  }

  // ---- Reception d'une reponse a notre offre ----
  function handleIncomingAnswer(data) {
    if (!callState.callId || callState.callId !== data.call_id || !peerConnection) return
    callLog('answer received', data.call_id)
    stopRingtone(ringtoneHandles)
    if (data.kind) {
      callState.kind = data.kind
      callControls.cameraEnabled = data.kind === 'video'
    }
    if (data.from_user_id && !callState.remoteUserId) {
      callState.remoteUserId = String(data.from_user_id)
    }
    const answer = data.sdp
    if (answer) {
      peerConnection.setRemoteDescription(answer).then(() => {
        flushPendingCandidates()
      }).catch(() => {})
    }
  }

  // ---- Reception d'une ICE candidate ----
  function handleIncomingCandidate(data) {
    if (!callState.callId || callState.callId !== data.call_id) return
    const candidate = data.candidate
    if (!candidate) return
    if (!peerConnection) {
      pendingIceCandidates.push(candidate)
      return
    }
    try {
      peerConnection.addIceCandidate(candidate)
    } catch {
      pendingIceCandidates.push(candidate)
    }
  }

  // ---- Fin d'appel distante ----
  function handleIncomingHangup(data) {
    if (!callState.callId || data.call_id !== callState.callId) return
    callLog('remote hangup', data.call_id, data.reason || '')
    endCall(true)
  }

  // ---- Bascule micro (et applique sur les tracks locales) ----
  function toggleMicrophone() {
    callControls.micEnabled = !callControls.micEnabled
    if (callState.localStream) {
      callState.localStream.getAudioTracks().forEach((track) => {
        track.enabled = callControls.micEnabled
      })
    }
  }

  // ---- Bascule camera (uniquement en mode video) ----
  function toggleCamera() {
    if (callState.kind !== 'video') return
    callControls.cameraEnabled = !callControls.cameraEnabled
    if (callState.localStream) {
      callState.localStream.getVideoTracks().forEach((track) => {
        track.enabled = callControls.cameraEnabled
      })
    }
  }

  // ---- Router des evenements temps reel (offer/answer/candidate/hangup) ----
  function handleCallSignal(evt) {
    const data = evt?.payload || {}
    const convId = data.conversation_id || evt.conversation_id
    if (!selectedConversationId.value || String(convId) !== String(selectedConversationId.value)) return
    const targetId = data.target_user_id ? String(data.target_user_id) : null
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    if (targetId && selfId && targetId !== selfId) return
    switch (evt.event) {
      case 'call:offer':
        handleIncomingOffer(data)
        break
      case 'call:answer':
        handleIncomingAnswer(data)
        break
      case 'call:candidate':
        handleIncomingCandidate(data)
        break
      case 'call:hangup':
        handleIncomingHangup(data)
        break
      default:
        break
    }
  }

  // ---- Associe les streams actuels aux refs audio/video (DOM) ----
  function ensureAttachTargets() {
    attachStream(localVideoRef.value, callState.localStream || null)
    attachStream(remoteVideoRef.value, callState.remoteStream || null)
    attachStream(remoteAudioRef.value, callState.remoteStream || null)
  }

  // ---- Permet de forcer une verification externe du peer (ex: onMounted) ----
  function ensurePeerReady() {
    ensurePeerConnectionReady(peerConnection)
  }

  watch(
    () => callState.localStream,
    (stream) => {
      attachStream(localVideoRef.value, stream || null)
    },
  )

  watch(
    () => callState.remoteStream,
    (stream) => {
      attachStream(remoteVideoRef.value, stream || null)
      attachStream(remoteAudioRef.value, stream || null)
    },
  )

  watch(localVideoRef, (el) => attachStream(el, callState.localStream || null))
  watch(remoteVideoRef, (el) => attachStream(el, callState.remoteStream || null))
  watch(remoteAudioRef, (el) => attachStream(el, callState.remoteStream || null))

  watch(
    () => callState.status,
    (status, prev) => {
      callLog('call status change', prev, '->', status)
      if (status === 'connected' || status === 'idle') {
        stopRingtone(ringtoneHandles)
      }
      if (status === 'incoming') {
        notifyIncomingSummary?.({
          callId: callState.callId,
          from: callState.remoteUserId,
          kind: callState.kind,
        })
      }
    },
  )

  return {
    callState,
    callControls,
    localVideoRef,
    remoteAudioRef,
    remoteVideoRef,
    remoteDisplayName,
    callStatusLabel,
    startCall,
    acceptIncomingCall,
    rejectIncomingCall: () => endCall(false, { reason: 'decline' }),
    cancelOutgoingCall: () => endCall(false, { reason: 'canceled' }),
    hangupCall: () => endCall(false, { reason: 'hangup' }),
    toggleMicrophone,
    toggleCamera,
    handleCallSignal,
    handleIncomingCandidate,
    handleIncomingAnswer,
    handleIncomingOffer,
    handleIncomingHangup,
    flushPendingCandidates,
    ensureAttachTargets,
    ensurePeerReady,
    endCall,
  }
}
