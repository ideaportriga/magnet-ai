<template lang="pug">
.full-width
  km-section(
    title='Transcription model',
    subTitle='Select transcription model to transcribe speech to text.'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Model
    km-select(
      v-model='pipelineId',
      :options='pipelineOptions',
      option-label='label',
      option-value='value',
      emit-value,
      map-options,
      height='30px'
    )

  q-separator.q-my-lg

  km-section(
    title='Limit max number of speakers',
    subTitle='For Scribe models, you can use either max number of speakers or diarization threshold parameters to help model detect speakers more accurately.'
  )
    .column.q-gap-16
      .column
        .row.items-baseline
          .col-auto.q-mr-sm
            q-toggle(v-model='sendNumberOfSpeakers', color='primary', dense)
          .col Send max number of speakers
        .km-description.text-secondary-text.q-mt-xs.q-ml-sm When enabled, Note Taker sends speaker count to transcription backend.
      .column.q-pl-8(v-if='sendNumberOfSpeakers')
        q-radio(
          v-model='maxSpeakerCountSource',
          val='invited',
          label='Send number of invited participants from the meeting',
          color='primary',
          dense
        )
        q-radio(
          v-model='maxSpeakerCountSource',
          val='manual',
          label='Manually set max speaker count',
          color='primary',
          dense
        )
        .row.q-mt-sm(v-if='maxSpeakerCountSource === "manual"')
          .col(style='max-width: 120px')
            km-input(
              v-model='maxSpeakerCount',
              type='number',
              placeholder='Max speaker count',
              height='30px',
              :min='1',
              :max='32'
            )
          .km-description.text-secondary-text.q-ml-sm Max value allowed: 32
      .column
        .row.items-baseline
          .col-auto.q-mr-sm
            q-toggle(v-model='diarizationThresholdEnabled', color='primary', dense)
          .col Diarization threshold
        .km-description.text-secondary-text.q-mt-xs.q-ml-sm When enabled, a higher value means less total speakers predicted.
      .column(v-if='diarizationThresholdEnabled')
        km-slider-card(
          v-model='diarizationThreshold',
          name='Diarization threshold',
          :min='0',
          :max='1',
          minLabel='More speakers',
          maxLabel='Less speakers',
          :defaultValue='0.2',
          :step='0.1',
          description='A higher value means there will be a lower chance of one speaker being diarized as two different speakers, but also a higher chance of two different speakers being diarized as one speaker.'
        )

  q-separator.q-my-lg

  km-section(
    title='Keyterms',
    subTitle='Optional keyterms to improve transcription and post-processing accuracy.'
  )
    .column.q-gap-12
      .row.q-gap-8(v-for='(entry, idx) in keytermsList', :key='idx')
        .col
          km-input(
            :model-value='entry.keyterm',
            placeholder='Keyterm',
            height='30px',
            @update:model-value='(v) => { entry.keyterm = v; syncKeytermsString() }'
          )
        .col
          km-input(
            :model-value='entry.description',
            placeholder='Description / Extra info (optional)',
            height='30px',
            @update:model-value='(v) => { entry.description = v; syncKeytermsString() }'
          )
        .col-auto
          q-btn(
            flat,
            dense,
            round,
            icon='delete',
            color='grey',
            @click='removeKeyterm(idx)'
          )
      km-btn(flat, icon='add', label='Add', @click='addKeyterm()')

  q-separator.q-my-lg

  km-section(
    title='Subscription for recordings',
    subTitle='Automatically create recordings-ready subscriptions for meetings.'
  )
    q-toggle(v-model='subscriptionRecordingsReady', color='primary', dense)
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()

const pipelineOptions = [
  { label: 'ElevenLabs', value: 'elevenlabs' },
  { label: 'Voxtral (Mistral)', value: 'mistral' },
  { label: 'Scribe 2.0', value: 'scribe' },
]

const subscriptionRecordingsReady = computed({
  get: () => store.getters.noteTakerSettings?.subscription_recordings_ready ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'subscription_recordings_ready', value })
  },
})

const pipelineId = computed({
  get: () => store.getters.noteTakerSettings?.pipeline_id || 'elevenlabs',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'pipeline_id', value })
  },
})

const sendNumberOfSpeakers = computed({
  get: () => store.getters.noteTakerSettings?.send_number_of_speakers ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'send_number_of_speakers', value })
  },
})

const maxSpeakerCountSource = ref('invited')
watch(
  () => store.getters.noteTakerSettings?.max_speaker_count_source,
  (val) => {
    if (val) maxSpeakerCountSource.value = val
  },
  { immediate: true }
)
watch(maxSpeakerCountSource, (val) => {
  store.dispatch('updateNoteTakerSetting', { path: 'max_speaker_count_source', value: val })
})

const maxSpeakerCount = computed({
  get: () => {
    const v = store.getters.noteTakerSettings?.max_speaker_count
    return v == null || v === '' ? '' : v
  },
  set: (value: number | string | null) => {
    const num = value == null || value === '' ? null : Number(value)
    store.dispatch('updateNoteTakerSetting', { path: 'max_speaker_count', value: num })
  },
})

const diarizationThresholdEnabled = computed({
  get: () => store.getters.noteTakerSettings?.diarization_threshold_enabled ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'diarization_threshold_enabled', value })
  },
})

const diarizationThreshold = computed({
  get: () => store.getters.noteTakerSettings?.diarization_threshold ?? 0.2,
  set: (value: number) => {
    store.dispatch('updateNoteTakerSetting', { path: 'diarization_threshold', value })
  },
})

function parseKeytermsList(settings: any): { keyterm: string; description: string }[] {
  const list = settings?.keyterms_list
  if (Array.isArray(list) && list.length) {
    return list.map((e: any) => ({
      keyterm: str(e?.keyterm),
      description: str(e?.description),
    }))
  }
  const strVal = str(settings?.keyterms || '')
  if (!strVal) return []
  return strVal.split(/[\n,;]+/).map((t) => ({ keyterm: t.trim(), description: '' })).filter((e) => e.keyterm)
}

function str(v: any): string {
  return String(v ?? '').trim()
}

const keytermsList = ref<{ keyterm: string; description: string }[]>([])

watch(
  () => store.getters.noteTakerSettings,
  (settings) => {
    keytermsList.value = parseKeytermsList(settings)
  },
  { immediate: true }
)

function syncKeytermsString() {
  const terms = keytermsList.value.filter((e) => e.keyterm).map((e) => e.keyterm)
  store.dispatch('updateNoteTakerSetting', { path: 'keyterms', value: terms.join('\n') })
  store.dispatch('updateNoteTakerSetting', {
    path: 'keyterms_list',
    value: keytermsList.value.filter((e) => e.keyterm || e.description).map((e) => ({ keyterm: e.keyterm, description: e.description })),
  })
}

function addKeyterm() {
  keytermsList.value.push({ keyterm: '', description: '' })
}

function removeKeyterm(idx: number) {
  keytermsList.value.splice(idx, 1)
  syncKeytermsString()
}
</script>
