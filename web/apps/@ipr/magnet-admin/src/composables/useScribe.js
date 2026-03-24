import { ref, onUnmounted } from 'vue'
import { Scribe, RealtimeEvents } from '@elevenlabs/client'

/**
 * Vue composable equivalent to React's useScribe from @elevenlabs/react.
 * Uses @elevenlabs/client Scribe for real-time speech-to-text.
 *
 * @param {Object} options
 * @param {string} [options.modelId='scribe_v2_realtime']
 * @param {Function} [options.onError] - (e) => void
 * @returns {{
 *   connect: (opts: { token: string, microphone?: { echoCancellation?: boolean, noiseSuppression?: boolean } }) => Promise<void>,
 *   disconnect: () => void,
 *   isConnected: import('vue').Ref<boolean>,
 *   status: import('vue').Ref<string>,
 *   partialTranscript: import('vue').Ref<string>,
 *   committedTranscripts: import('vue').Ref<Array<{ id: string, text: string }>>,
 *   error: import('vue').Ref<string|null>,
 *   clearTranscripts: () => void
 * }}
 */
export function useScribe(options = {}) {
  const modelId = options.modelId ?? 'scribe_v2_realtime'
  const onErrorCallback = options.onError

  const status = ref('disconnected')
  const isConnected = ref(false)
  const isPaused = ref(false)
  const partialTranscript = ref('')
  const committedTranscripts = ref([])
  const error = ref(null)

  let connection = null
  let lastConnectOptions = null

  function setError(e) {
    const msg = e?.message ?? e?.error ?? (typeof e === 'string' ? e : 'Unknown error')
    error.value = msg
    onErrorCallback?.(e)
  }

  function clearError() {
    error.value = null
  }

  function clearTranscripts() {
    partialTranscript.value = ''
    committedTranscripts.value = []
  }

  function disconnect() {
    if (connection) {
      try {
        connection.close()
      } catch (err) {
        console.warn('Scribe disconnect error:', err)
      }
      connection = null
    }
    status.value = 'disconnected'
    isConnected.value = false
    isPaused.value = false
    partialTranscript.value = ''
  }

  function pause() {
    if (!connection) return
    if (typeof connection.commit === 'function') {
      connection.commit()
    }
    if (typeof connection._audioCleanup === 'function') {
      connection._audioCleanup()
      connection._audioCleanup = undefined
    }
    isPaused.value = true
  }

  async function resume() {
    if (!connection || !lastConnectOptions) return
    try {
      if (typeof Scribe.streamFromMicrophone === 'function') {
        await Scribe.streamFromMicrophone(lastConnectOptions, connection)
      }
      isPaused.value = false
    } catch (err) {
      setError(err)
    }
  }

  async function connect(connectOptions = {}) {
    const token = connectOptions.token
    if (!token) {
      setError(new Error('Token is required to connect'))
      return
    }
    disconnect()
    clearError()
    status.value = 'connecting'
    try {
      const opts = {
        token,
        modelId,
        microphone: {
          echoCancellation: connectOptions.microphone?.echoCancellation ?? true,
          noiseSuppression: connectOptions.microphone?.noiseSuppression ?? true,
        },
      }
      lastConnectOptions = opts
      connection = Scribe.connect(opts)

      connection.on(RealtimeEvents.OPEN, () => {
        console.log('Scribe connected')
        status.value = 'connected'
        isConnected.value = true
      })

      connection.on(RealtimeEvents.SESSION_STARTED, () => {
        console.log('Scribe session started')
        status.value = 'transcribing'
        isConnected.value = true
      })

      connection.on(RealtimeEvents.PARTIAL_TRANSCRIPT, (data) => {
        console.log('Scribe partial transcript', data)
        const text = data?.text ?? data?.transcript ?? data?.partial_transcript?.text ?? ''
        partialTranscript.value = text
      })

      connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT, (data) => {
        console.log('Scribe committed transcript', data)
        const text = data.transcript ?? data.text ?? ''
        const id = data.transcript_id ?? data.id ?? `t-${Date.now()}-${Math.random().toString(36).slice(2)}`
        committedTranscripts.value = [...committedTranscripts.value, { id, text }]
        partialTranscript.value = ''
      })

      connection.on(RealtimeEvents.CLOSE, () => {
        console.log('Scribe closed')
        disconnect()
      })

      connection.on(RealtimeEvents.ERROR, (data) => {
        const msg = data?.message ?? data?.error ?? data?.reason ?? (data instanceof Error ? data.message : String(data))
        setError(msg)
      })
    } catch (err) {
      status.value = 'disconnected'
      setError(err)
      connection = null
    }
  }

  onUnmounted(() => {
    if (isConnected.value) {
      disconnect()
    }
  })

  return {
    connect,
    disconnect,
    pause,
    resume,
    isConnected,
    isPaused,
    status,
    partialTranscript,
    committedTranscripts,
    error,
    clearTranscripts,
  }
}
