<template>
  <div>
    <km-section title="Transcription model" sub-title="Select transcription model to transcribe speech to text">
      <div class="km-field text-secondary-text pb-xs pl-sm">Model</div>
      <km-select v-model="pipelineId" :options="pipelineOptions" option-label="label" option-value="value" emit-value map-options height="auto" min-height="36px" />
      <div class="km-description text-secondary-text pt-xs pl-sm">Speech to text transcription model</div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Limit max number of speakers" sub-title="For some models, you can use max number of speakers or diarization threshold parameters to help model detect speakers more accurately.">
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Send max number of speakers</div>
        <km-toggle v-model="sendNumberOfSpeakers" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">When enabled, Note Taker sends speaker count to transcription backend.</div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Keyterms" sub-title="Keyterms to improve transcription accuracy">
      <div class="km-field text-secondary-text pb-xs pl-sm">Keyterms</div>
      <km-input v-model="keyterms" class="full-width" type="textarea" autogrow :rows="3" height="36px" min-height="80px" border-radius="8px" :placeholder="m.noteTaker_exampleKeyterms()" />
      <div class="km-description text-secondary-text pt-xs pl-sm">Comma separated</div>
    </km-section>
  </div>
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
  { label: 'Default (auto)', value: '__auto__' },
])

const pipelineId = computed({
  get: () => ntStore.settings?.pipeline_id || '__auto__',
  set: (v: string) => ntStore.updateSetting({ path: 'pipeline_id', value: v === '__auto__' ? '' : v }),
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
        { label: 'Default (auto)', value: '__auto__' },
        ...items.map((m: any) => ({ label: m.name || m.system_name, value: m.system_name })),
      ]
    }
  } catch { /* ignore */ }
}

watch(apiReady, (ready) => {
  if (ready) fetchSttModels()
}, { immediate: true })
</script>
