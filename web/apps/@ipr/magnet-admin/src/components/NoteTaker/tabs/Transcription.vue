<template lang="pug">
div
  km-section(title='Transcription model', subTitle='Select transcription model to transcribe speech to text')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Model
    km-select(
      v-model='pipelineId',
      :options='pipelineOptions',
      option-label='label',
      option-value='value',
      emit-value,
      map-options,
      height='auto',
      minHeight='36px'
    )
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Speech to text transcription model

  q-separator.q-my-lg

  km-section(title='Limit max number of speakers', subTitle='For some models, you can use max number of speakers or diarization threshold parameters to help model detect speakers more accurately.')
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Send max number of speakers
      q-toggle(v-model='sendNumberOfSpeakers', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 When enabled, Note Taker sends speaker count to transcription backend.

  q-separator.q-my-lg

  km-section(title='Keyterms', subTitle='Keyterms to improve transcription accuracy')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Keyterms
    km-input.full-width(
      type='textarea',
      autogrow,
      :rows='3',
      height='36px',
      minHeight='80px',
      border-radius='8px',
      placeholder='e.g. Primeks, Magnet, LIAA, Reckitt',
      v-model='keyterms'
    )
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Comma separated
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { fetchData } from '@shared'

const ntStore = useNoteTakerStore()
const appStore = useAppStore()

const pipelineOptions = ref<{ label: string; value: string }[]>([
  { label: 'Default (auto)', value: '' },
])

const pipelineId = computed({
  get: () => ntStore.settings?.pipeline_id ?? '',
  set: (v: string) => ntStore.updateSetting( { path: 'pipeline_id', value: v }),
})
const sendNumberOfSpeakers = computed({
  get: () => ntStore.settings?.send_number_of_speakers ?? false,
  set: (v: boolean) => ntStore.updateSetting( { path: 'send_number_of_speakers', value: v }),
})
const keyterms = computed({
  get: () => ntStore.settings?.keyterms || '',
  set: (v: string) => ntStore.updateSetting( { path: 'keyterms', value: v }),
})

const apiReady = computed(() => Boolean(appStore.config?.api?.aiBridge?.urlAdmin))

const fetchSttModels = async () => {
  const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
  if (!endpoint) return
  try {
    const response = await fetchData({
      method: 'GET', endpoint, service: 'models/?type=stt&pagination_size=100',
      credentials: 'include', headers: { Accept: 'application/json' },
    })
    if (!response?.ok) return
    const data = await response.json()
    const items: any[] = Array.isArray(data) ? data : (data?.items || data?.data || [])
    if (items.length > 0) {
      pipelineOptions.value = [
        { label: 'Default (auto)', value: '' },
        ...items.map((m: any) => ({ label: m.name || m.system_name, value: m.system_name })),
      ]
    }
  } catch { /* ignore */ }
}

watch(apiReady, (ready) => {
  if (ready) fetchSttModels()
}, { immediate: true })
</script>
