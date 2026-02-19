<template lang="pug">
q-dialog(:model-value='modelValue', persistent, @update:model-value='$emit("update:modelValue", $event)')
  q-card(style='min-width: 500px')
    q-card-section
      .text-h6 Start Run
    q-card-section.q-pt-none
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs Config
        km-input(
          :model-value='configName',
          height='30px',
          readonly
        )
        .km-description.text-secondary-text.q-pt-2 This run will use the current configuration
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs File
        q-file(
          v-model='runFile',
          outlined,
          dense,
          clearable,
          use-chips,
          bottom-slots,
          label='Choose file',
          hint='Select audio/video file for transcription',
          accept='.mp3,.mp4,.m4a,.wav,.webm,.ogg,.flac',
          @rejected='onFileRejected'
        )
          template(#prepend)
            q-icon(name='fas fa-file')
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs Language
        km-input(
          v-model='runLanguage',
          height='30px',
          placeholder='e.g. en'
        )
        .km-description.text-secondary-text.q-pt-2 Language code (e.g. en, es)
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs Speaker settings
        km-input(
          :model-value='speakerSettingsText',
          height='30px',
          readonly
        )
    q-card-actions(align='right')
      km-btn(flat, label='Cancel', @click='close')
      km-btn(label='Start Run', :loading='startingRun', :disable='!canStartRun', @click='startRun')
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useStore } from 'vuex'
import { fetchData } from '@shared'

defineProps({
  modelValue: { type: Boolean, default: false },
  configName: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const store = useStore()
const $q = useQuasar()
const startingRun = ref(false)
const runFile = ref(null)
const runLanguage = ref('en')
const runFileError = ref('')

const canStartRun = computed(() => runFile.value && runLanguage.value?.trim())

const speakerSettingsText = computed(() => {
  const settings = store.getters.noteTakerSettings || {}
  if (settings.send_number_of_speakers && settings.max_speaker_count_source === 'manual' && settings.max_speaker_count != null) {
    return `Max speakers: ${settings.max_speaker_count}`
  }
  if (settings.diarization_threshold_enabled && settings.diarization_threshold != null) {
    const thr = Math.max(0.1, Math.min(0.4, Number(settings.diarization_threshold)))
    return `Diarization threshold: ${thr}`
  }
  return 'Auto'
})

watch(() => runFile.value, () => { runFileError.value = '' })

const onFileRejected = () => {
  runFileError.value = 'Invalid file type or size.'
}

const close = () => {
  emit('update:modelValue', false)
  runFile.value = null
  runLanguage.value = 'en'
  runFileError.value = ''
}

async function uploadFile(url, file, headers) {
  const res = await fetch(url, { method: 'PUT', headers: headers || {}, body: file })
  console.log(res)
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
}

const startRun = async () => {
  if (!canStartRun.value) return
  const file = runFile.value
  if (!(file instanceof File)) return

  startingRun.value = true
  runFileError.value = ''
  try {
    const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
    const settings = store.getters.noteTakerSettings || {}
    //"https://magnetaistorage.blob.core.windows.net/uploads/2026/02/19/d3ae9dc8-8b2b-446b-9d98-65e231d4a8af-22801d56-3a37-4a7a-bb05-bd4d6fdae7ce.mp4?se=2026-02-19T12%3A38%3A12Z&sp=cw&sv=2026-02-06&sr=b&sig=ldkexKvbR2%2B1SnHFckdRJ%2BAksl%2BCy0aN27wJatAslSM%3D"
    //"https://magnetaistorage.blob.core.windows.net/uploads/2026/02/19/d3ae9dc8-8b2b-446b-9d98-65e231d4a8af-22801d56-3a37-4a7a-bb05-bd4d6fdae7ce.mp4?se=2026-02-19T12%3A38%3A12Z&sp=cw&sv=2026-02-06&sr=b&sig=ldkexKvbR2%2B1SnHFckdRJ%2BAksl%2BCy0aN27wJatAslSM%3D"
    // Step 1: Create upload session
    const sessionRes = await fetchData({
      endpoint,
      service: 'upload-sessions',
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify({
        filename: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
      }),
      headers: { 'Content-Type': 'application/json' },
    })
    if (sessionRes?.error) throw new Error(sessionRes.error?.message || 'Failed to create upload session')
    if (!sessionRes?.ok) {
      const errData = await sessionRes?.json?.().catch(() => ({}))
      throw new Error(errData?.detail || errData?.error || 'Failed to create upload session')
    }
    const session = await sessionRes.json()
    const { object_key, upload_url, upload_headers } = session
    if (!object_key || !upload_url) throw new Error('Invalid upload session response')

    // Step 2: Upload file to storage URL
    const uploadHeaders = upload_headers || {}
    // iOS Safari fix: Convert File to Blob and ensure proper Content-Type
    const fileBlob = file instanceof File ? new Blob([file], { type: file.type }) : file
    const headers = {
      ...uploadHeaders,
      'Content-Type': file.type || 'application/octet-stream',
    }
    await uploadFile(upload_url, fileBlob, headers)

    // Step 3: Start transcription with object_key
    const payload = {
      object_key,
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      language: runLanguage.value.trim(),
      pipeline_id: settings.pipeline_id || 'elevenlabs',
    }
    if (settings.keyterms) {
      const terms = settings.keyterms.split(/[\n,]/).map((t) => t.trim()).filter(Boolean)
      if (terms.length) payload.keyterms = terms
    }
    if (settings.send_number_of_speakers && settings.max_speaker_count_source === 'manual' && settings.max_speaker_count != null) {
      payload.number_of_participants = String(settings.max_speaker_count)
    } else if (settings.diarization_threshold_enabled && settings.diarization_threshold != null) {
      const thr = Math.max(0.1, Math.min(0.4, Number(settings.diarization_threshold)))
      payload.diarization_threshold = String(thr)
    }

    const response = await fetchData({
      endpoint,
      service: 'recordings',
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })

    if (response?.error) throw new Error(response.error?.message || 'Failed to start run')
    if (response?.ok) {
      const data = await response.json()
      $q.notify({
        position: 'top',
        message: `Run started. Job ID: ${data?.id || 'N/A'}`,
        color: 'positive',
        textColor: 'black',
        timeout: 2000,
      })
      close()
    } else {
      const errData = await response?.json?.().catch(() => ({}))
      throw new Error(errData?.detail || errData?.error || response?.statusText || 'Failed to start run')
    }
  } catch (err) {
    runFileError.value = err?.message || 'Failed to start run'
    $q.notify({
      position: 'top',
      message: err?.message || 'Failed to start run',
      color: 'negative',
      textColor: 'white',
      timeout: 3000,
    })
  } finally {
    startingRun.value = false
  }
}
</script>
