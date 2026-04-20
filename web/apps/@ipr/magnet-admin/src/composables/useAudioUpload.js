import { ref } from 'vue'
import { fetchData } from '@shared'

const ALLOWED_EXT = ['.flac', '.m4a', '.mp3', '.ogg', '.wav', '.webm', '.mp4']

const POLL_INTERVAL_MS = 2000
const MAX_POLL_MS = 30 * 60 * 1000 // §B.2 — 30 min ceiling
const DONE_STATUSES = ['transcribed', 'completed', 'diarized']

/**
 * Composable for audio upload and transcription flow.
 * Steps: 1) create session, 2) upload file to blob, 3) start transcription, 4) poll until result.
 *
 * @param {Object} options
 * @param {string} options.endpoint - API base URL (e.g. store.getters.config.api.aiBridge.urlAdmin)
 * @param {string} [options.credentials='include']
 * @param {string} [options.language='en']
 * @returns {{
 *   uploadAndTranscribe: (file: File) => Promise<{ segments: Array, jobId: string }>,
 *   isUploading: import('vue').Ref<boolean>,
 *   uploadStatus: import('vue').Ref<string>,
 *   error: import('vue').Ref<string|null>,
 *   reset: () => void
 * }}
 */
export function useAudioUpload(options = {}) {
  const getEndpoint = typeof options.endpoint === 'function' ? options.endpoint : () => options.endpoint ?? ''
  const credentials = options.credentials ?? 'include'
  const language = options.language ?? 'en'

  const isUploading = ref(false)
  const uploadStatus = ref('')
  const error = ref(null)

  function reset() {
    isUploading.value = false
    uploadStatus.value = ''
    error.value = null
  }

  function assertAllowedExt(filename) {
    const ext = '.' + (filename.split('.').pop() || '').toLowerCase()
    if (!ALLOWED_EXT.includes(ext)) {
      throw new Error(`Unsupported format. Allowed: ${ALLOWED_EXT.join(', ')}`)
    }
  }

  async function createSession(file) {
    const endpoint = getEndpoint()
    const res = await fetchData({
      method: 'POST',
      endpoint,
      credentials,
      service: 'upload-sessions',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
      }),
    })
    if (res.error) throw res.error
    const data = await res.json()
    if (!data.upload_url || !data.object_key) {
      throw new Error('Invalid session response')
    }
    return data
  }

  async function uploadToBlob(session, file) {
    const headers = { ...(session.upload_headers || {}) }
    if (!headers['Content-Type']) {
      headers['Content-Type'] = file.type || 'application/octet-stream'
    }
    const body = file instanceof File ? file : new Blob([file], { type: file.type })
    const res = await fetch(session.upload_url, {
      method: 'PUT',
      headers,
      body,
      credentials: 'omit',
    })
    if (!res.ok) {
      const errText = await res.text()
      throw new Error(errText || `Upload failed: ${res.status}`)
    }
  }

  async function startTranscription(session, file) {
    const endpoint = getEndpoint()
    const res = await fetchData({
      method: 'POST',
      endpoint,
      credentials,
      service: 'recordings',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        object_key: session.object_key,
        filename: file.name,
        content_type: file.type || 'application/octet-stream',
        language,
      }),
    })
    if (res.error) throw res.error
    const data = await res.json()
    if (!data.id) throw new Error('No job ID returned')
    return data.id
  }

  // §B.2: bounded poll loop so a stuck backend can't grow memory forever.
  // 30 min is comfortably beyond any legitimate transcription; beyond that
  // we surface an error so the caller can cancel/retry instead of hanging.
  async function pollForResult(jobId) {
    const endpoint = getEndpoint()
    const deadline = Date.now() + MAX_POLL_MS
    while (Date.now() < deadline) {
      const res = await fetchData({
        method: 'GET',
        endpoint,
        credentials,
        service: `recordings/${jobId}`,
      })
      if (res.error) throw res.error
      const data = await res.json()
      const status = data.status || 'unknown'

      if (status === 'failed') {
        const errMsg = data.error || 'Transcription failed'
        throw new Error(errMsg)
      }

      if (DONE_STATUSES.includes(status)) {
        const meta = data.transcription_job || data
        const tx = meta.transcription
        const segments = (tx && tx.segments) || []
        const text = (tx && tx.text) || ''
        return { segments, text, meta }
      }

      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
    }
    throw new Error('Transcription polling timed out after 30 minutes')
  }

  async function uploadAndTranscribe(file) {
    if (!file) throw new Error('File is required')
    assertAllowedExt(file.name)

    isUploading.value = true
    uploadStatus.value = 'Creating session…'
    error.value = null

    try {
      const session = await createSession(file)

      uploadStatus.value = 'Uploading…'
      await uploadToBlob(session, file)

      uploadStatus.value = 'Starting transcription…'
      const jobId = await startTranscription(session, file)

      uploadStatus.value = 'Transcribing…'
      const { segments } = await pollForResult(jobId)

      uploadStatus.value = ''
      return { segments, jobId }
    } catch (e) {
      error.value = e?.message ?? e?.technicalError ?? String(e)
      throw e
    } finally {
      isUploading.value = false
    }
  }

  return {
    uploadAndTranscribe,
    isUploading,
    uploadStatus,
    error,
    reset,
    ALLOWED_EXT,
  }
}
