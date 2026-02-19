<template lang="pug">
.full-width
  km-section(
    title='Transcription model',
    subTitle='Select transcription model to transcribe speech to text.'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Model
    .row.items-center.q-gap-16.no-wrap
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

  km-section.speaker-settings-radios(
    title='Limit max number of speakers',
    subTitle='For Scribe models, you can use either max number of speakers or diarization threshold parameters to help model detect speakers more accurately.'
  )
    .column.q-gap-16
      .column.q-gap-8
        .row.items-center.q-gap-8
          q-radio(
            v-model='speakerMode',
            val='none',
            label='Auto',
            color='primary',
            dense
          )
          q-icon(name='o_info', color='text-secondary', size='16px')
            q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') Let the model automatically detect speakers without hints.
        .row.items-center.q-gap-8
          q-radio(
            v-model='speakerMode',
            val='speakers',
            label='Send max number of speakers',
            color='primary',
            dense
          )
          q-icon(name='o_info', color='text-secondary', size='16px')
            q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') Note Taker sends speaker count to transcription backend.
        .row.items-center.q-gap-8
          q-radio(
            v-model='speakerMode',
            val='threshold',
            label='Diarization threshold',
            color='primary',
            dense
          )
          q-icon(name='o_info', color='text-secondary', size='16px')
            q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') A higher value means less total speakers predicted.
      q-separator.q-my-sm(v-if='speakerMode === "speakers" || speakerMode === "threshold"')
      .column.q-pl-8.q-gap-8(v-if='speakerMode === "speakers"')
        .row.items-center.q-gap-8
          q-radio(
            v-model='maxSpeakerCountSource',
            val='invited',
            label='Send number of invited participants from the meeting',
            color='primary',
            dense
          )
        .row.items-center.q-gap-8
          q-radio(
            v-model='maxSpeakerCountSource',
            val='manual',
            label='Manually set max speaker count',
            color='primary',
            dense
          )
        .row.q-mt-sm(v-if='maxSpeakerCountSource === "manual"')
          .col(style='max-width: 120px')
            .row.items-center.q-gap-8
              .km-field.text-secondary-text.q-pb-xs.q-pl-8 Max speaker count
            .row.items-center.q-gap-16.no-wrap
              km-input(
                v-model='maxSpeakerCount',
                type='number',
                height='30px',
                :min='1',
                :max='32'
              )
      .column.q-pl-8(v-if='speakerMode === "threshold"')
        km-slider-card(
          v-model='diarizationThreshold',
          name='Diarization threshold',
          :min='0.1',
          :max='0.4',
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
    .row.items-center.q-gap-8.no-wrap.q-mt-sm(v-for='(entry, idx) in keytermsList', :key='idx')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Keyterm
        km-input(
          :model-value='entry.keyterm',
          height='30px',
          @update:model-value='(v) => { entry.keyterm = v; syncKeytermsString() }'
        )
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description / Extra info (optional)
        km-input(
          :model-value='entry.description',
          height='30px',
          @update:model-value='(v) => { entry.description = v; syncKeytermsString() }'
        )
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeKeyterm(idx)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(label='Add', @click='addKeyterm()', size='sm', icon='o_add', flat)

  q-separator.q-my-lg

  km-section(
    title='Subscription for recordings ready',
    subTitle='Automatically create recordings-ready subscriptions for meetings.'
  )
    q-toggle(v-model='subscriptionRecordingsReady', color='primary', dense)

  q-separator.q-my-lg

  km-section(
    title='Accept commands from non-organizer',
    subTitle='Off by default. If switched on, Note Taker will accept commands from users other than meeting organizer.'
  )
    q-toggle(v-model='acceptCommandsFromNonOrganizer', color='primary', dense)
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

const acceptCommandsFromNonOrganizer = computed({
  get: () => store.getters.noteTakerSettings?.accept_commands_from_non_organizer ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'accept_commands_from_non_organizer', value })
  },
})

const pipelineId = computed({
  get: () => store.getters.noteTakerSettings?.pipeline_id || 'elevenlabs',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'pipeline_id', value })
  },
})

const speakerMode = computed({
  get: () => {
    const settings = store.getters.noteTakerSettings
    if (settings?.send_number_of_speakers) return 'speakers'
    if (settings?.diarization_threshold_enabled) return 'threshold'
    return 'none'
  },
  set: (value: 'none' | 'speakers' | 'threshold') => {
    if (value === 'speakers') {
      store.dispatch('updateNoteTakerSetting', { path: 'send_number_of_speakers', value: true })
      store.dispatch('updateNoteTakerSetting', { path: 'diarization_threshold_enabled', value: false })
    } else if (value === 'threshold') {
      store.dispatch('updateNoteTakerSetting', { path: 'send_number_of_speakers', value: false })
      store.dispatch('updateNoteTakerSetting', { path: 'diarization_threshold_enabled', value: true })
    } else {
      store.dispatch('updateNoteTakerSetting', { path: 'send_number_of_speakers', value: false })
      store.dispatch('updateNoteTakerSetting', { path: 'diarization_threshold_enabled', value: false })
    }
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

const diarizationThreshold = computed({
  get: () => {
    const v = store.getters.noteTakerSettings?.diarization_threshold ?? 0.2
    return Math.max(0.1, Math.min(0.4, Number(v)))
  },
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

<style scoped>
.speaker-settings-radios :deep(.q-radio__label) {
  font-family: var(--font-default);
  font-size: 14px;
  font-weight: 400;
  color: var(--q-text-weak);
}
</style>
