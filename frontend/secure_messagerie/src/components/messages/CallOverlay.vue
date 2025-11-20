<template>
  <div
    v-if="callState.status !== 'idle'"
    class="call-overlay"
    role="dialog"
    aria-modal="true"
    :aria-label="callStatusLabel"
  >
    <div class="call-panel">
      <header class="call-panel__header">
        <div>
          <p class="call-panel__eyebrow">{{ callState.kind === 'video' ? 'Appel vidéo' : 'Appel audio' }}</p>
          <h4>{{ callStatusLabel }}</h4>
          <p class="call-panel__subtitle">{{ remoteDisplayName }}</p>
        </div>
      </header>
      <div
        class="call-video"
        :class="{ 'call-video--audio': callState.kind !== 'video' }"
      >
        <div class="call-remote">
          <template v-if="callState.kind === 'video'">
            <video
              :ref="setRemoteVideoRef"
              autoplay
              playsinline
              class="call-video__stream"
              :class="{ 'call-video__stream--hidden': !callState.remoteStream }"
            ></video>
          </template>
          <div v-else class="call-audio-placeholder">
            <i class="bi bi-person-fill"></i>
          </div>
          <p class="call-remote__label">{{ remoteDisplayName }}</p>
        </div>
        <div v-if="callState.kind === 'video'" class="call-local">
          <video
            :ref="setLocalVideoRef"
            autoplay
            muted
            playsinline
            class="call-video__stream call-video__stream--local"
          ></video>
          <p class="call-local__label">Vous</p>
        </div>
      </div>
      <p v-if="callState.error" class="msg-alert mt-2">{{ callState.error }}</p>
      <div class="call-controls">
        <template v-if="callState.status === 'incoming'">
          <button type="button" class="btn btn-success" @click="acceptIncomingCall">
            <i class="bi bi-telephone-inbound-fill me-1"></i>
            Répondre
          </button>
          <button type="button" class="btn btn-secondary" @click="rejectIncomingCall">
            Refuser
          </button>
        </template>
        <template v-else-if="callState.status === 'outgoing'">
          <button type="button" class="btn btn-secondary" @click="cancelOutgoingCall">
            Annuler l'appel
          </button>
        </template>
        <div v-if="callState.status === 'connected'" class="call-controls__toggles">
          <button
            type="button"
            class="btn"
            :class="{ 'is-muted': !callControls.micEnabled }"
            @click="toggleMicrophone"
          >
            <i :class="callControls.micEnabled ? 'bi bi-mic-fill' : 'bi bi-mic-mute-fill'"></i>
          </button>
          <button
            v-if="callState.kind === 'video'"
            type="button"
            class="btn"
            :class="{ 'is-muted': !callControls.cameraEnabled }"
            @click="toggleCamera"
          >
            <i :class="callControls.cameraEnabled ? 'bi bi-camera-video-fill' : 'bi bi-camera-video-off-fill'"></i>
          </button>
        </div>
        <button
          v-if="callState.status !== 'incoming'"
          type="button"
          class="btn btn-danger"
          @click="hangupCall"
        >
          <i class="bi bi-telephone-x-fill me-1"></i>
          Raccrocher
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  callState: {
    type: Object,
    required: true,
  },
  callStatusLabel: {
    type: String,
    required: true,
  },
  remoteDisplayName: {
    type: String,
    default: '',
  },
  callControls: {
    type: Object,
    required: true,
  },
  acceptIncomingCall: {
    type: Function,
    required: true,
  },
  rejectIncomingCall: {
    type: Function,
    required: true,
  },
  cancelOutgoingCall: {
    type: Function,
    required: true,
  },
  hangupCall: {
    type: Function,
    required: true,
  },
  toggleMicrophone: {
    type: Function,
    required: true,
  },
  toggleCamera: {
    type: Function,
    required: true,
  },
  setRemoteVideoRef: {
    type: Function,
    required: true,
  },
  setLocalVideoRef: {
    type: Function,
    required: true,
  },
})
</script>
