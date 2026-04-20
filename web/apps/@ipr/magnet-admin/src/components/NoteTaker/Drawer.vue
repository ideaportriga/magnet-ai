<template lang="pug">
km-drawer-layout(storageKey="drawer-note-taker", noScroll)
  template(#header)
    .row.items-center.full-width
      .col.km-heading-7 Preview
      .col-auto(v-if='currentJob')
        q-btn(
          flat, dense, size='sm', color='grey-7',
          icon='restart_alt', :label='m.common_startOver()',
          @click='resetPreview', no-caps
        )
    .km-description.text-secondary-text.q-mb-sm(v-if='!currentJob') Test your note taker configuration with a recording.

    //- Progress steps (only when job active)
    template(v-if='currentJob')
      .row.items-center.q-gap-8.q-py-sm
        template(v-for='(step, i) in pipelineSteps', :key='step.key')
          .row.items-center.q-gap-4(v-if='i > 0')
            q-icon(name='chevron_right', size='16px', color='grey-4')
          q-chip(
            dense, size='sm', square,
            :color='step.color', :text-color='step.textColor',
            :icon='step.icon'
          ) {{ step.label }}
      q-separator

  .column.full-height.full-width.no-wrap

    //- ══ SCROLLABLE CONTENT ════════════════════════════════════════════
    q-scroll-area.col(style='min-height: 0')

      //- ── No active job: input form ─────────────────────────────────
      template(v-if='!currentJob')
        .q-pt-md.q-pr-xs

          //- Source card
          q-card.q-mb-md(flat, bordered)
            q-card-section
              .row.items-center.q-mb-xs
                q-icon.q-mr-xs(name='audio_file', size='18px', color='grey-7')
                .km-heading-8 Recording source
              template(v-if='selectedFile')
                .row.items-center.no-wrap.q-gap-4
                  q-chip(
                    removable, color='primary-light', text-color='primary', icon='attach_file',
                    @remove='clearFile'
                  ) {{ selectedFile.name }}
                  q-btn(
                    flat, dense, round, size='sm',
                    icon='swap_horiz', color='grey-7',
                    @click='fileInput?.click()'
                  )
                    q-tooltip Choose another file
              template(v-else)
                .row.items-center.no-wrap.q-gap-4
                  km-input.col(
                    v-model='sourceUrl',
                    :placeholder='m.noteTaker_pasteRecordingUrl()',
                    height='32px', clearable
                  )
                  q-btn.col-auto(
                    flat, dense, round, size='sm',
                    icon='attach_file', color='grey-7',
                    @click='fileInput?.click()'
                  )
                    q-tooltip Attach file
              input(ref='fileInput', type='file', accept='audio/*,video/*,.mp4,.mp3,.wav,.m4a,.ogg,.webm,.mkv,.flac', style='display:none', @change='onFileSelected')

          //- Participants card
          q-card.q-mb-md(flat, bordered)
            q-card-section
              .row.items-center.q-mb-xs
                q-icon.q-mr-xs(name='people', size='18px', color='grey-7')
                .km-heading-8 Participants
              .km-description.text-secondary-text.q-mb-sm Optional. Helps with speaker identification.
              .row.items-center.q-gap-8
                km-input.col(
                  v-model='newParticipant',
                  :placeholder='m.noteTaker_fullName()',
                  height='32px',
                  @keyup.enter='addParticipant'
                )
                q-btn.col-auto(
                  flat, dense, round, size='sm',
                  icon='add', color='primary',
                  @click='addParticipant', :disable='!newParticipant.trim()'
                )
              .row.q-gap-4.q-flex-wrap.q-mt-sm(v-if='participants.length')
                q-chip(
                  v-for='(p, i) in participants', :key='i',
                  removable, color='primary-light', text-color='primary',
                  @remove='participants.splice(i, 1)'
                ) {{ p }}

      //- ── Active job content ────────────────────────────────────────
      template(v-if='currentJob')
        .q-py-md.q-pr-xs

          //- Transcribing
          template(v-if='["running","pending"].includes(currentJob.status)')
            q-card.q-pa-md(flat, bordered)
              .row.items-center.q-gap-12
                q-spinner-dots(color='primary', size='2em')
                .column
                  .km-heading-8 Transcribing...
                  .km-description.text-secondary-text This may take a few minutes depending on the recording length.

          //- Post-processing
          template(v-else-if='currentJob.status === "rerunning"')
            q-card.q-pa-md(flat, bordered)
              .row.items-center.q-gap-12
                q-spinner-dots(color='primary', size='2em')
                .column
                  .km-heading-8 Generating summary and chapters...
                  .km-description.text-secondary-text Running configured prompt templates.

          //- Failed
          template(v-else-if='currentJob.status === "failed"')
            q-banner.bg-red-1.text-negative.border-radius-6(dense)
              template(v-slot:avatar)
                q-icon(name='error_outline', color='negative')
              .km-heading-8 Pipeline failed
              .km-description.q-mt-4(style='word-break: break-word') {{ currentJob.result?.error || 'Unknown error' }}

          //- Transcribed: review speakers
          template(v-else-if='currentJob.status === "transcribed" && currentJob.result')
            q-card.q-mb-md(flat, bordered)
              q-card-section
                .row.items-center.q-mb-xs
                  q-icon.q-mr-xs(name='description', size='18px', color='grey-7')
                  .km-heading-8 Transcript
                q-input(
                  :modelValue='currentJob.result.full_text || ""',
                  type='textarea', outlined, dense, readonly, autogrow,
                  input-style='font-size: 12px; font-family: var(--km-font-mono); line-height: 1.5',
                  style='max-height: 250px; overflow-y: auto'
                )

            q-card.q-mb-md(flat, bordered, v-if='speakerLabels.length')
              q-card-section
                .row.items-center.q-mb-xs
                  q-icon.q-mr-xs(name='people', size='18px', color='grey-7')
                  .km-heading-8 Speaker Mapping
                .km-description.text-secondary-text.q-mb-sm Assign real names to detected speakers. Leave empty to keep the label.
                .q-gutter-sm
                  .row.items-center.q-gap-8(v-for='label in speakerLabels', :key='label')
                    q-chip.col-auto(dense, size='sm', square, color='blue-grey-1') {{ label }}
                    .col
                      km-input(v-model='speakerMapping[label]', :placeholder='m.noteTaker_nameForLabel({ label })', height='32px')

            q-card.q-mb-md(flat, bordered)
              q-card-section
                .km-heading-8.q-mb-sm Additional context
                .km-description.text-secondary-text.q-mb-xs Key terms (comma-separated)
                km-input.q-mb-sm(v-model='extraKeytermsInput', :placeholder='m.noteTaker_productNamesAcronyms()', height='32px')
                .km-description.text-secondary-text.q-mb-xs Meeting notes (optional)
                km-input(v-model='meetingNotesInput', :placeholder='m.noteTaker_actionItemsDecisions()', height='60px')

          //- Completed: results
          template(v-else-if='currentJob.status === "completed" && currentJob.result')
            q-card.q-mb-md(flat, bordered, v-if='currentJob.result.full_text')
              q-expansion-item(dense, header-class='q-pa-sm', :default-opened='false')
                template(v-slot:header)
                  .row.items-center.q-gap-4
                    q-icon(name='description', size='18px', color='grey-7')
                    .km-heading-8 Transcript
                q-card-section
                  q-input(
                    :modelValue='currentJob.result.full_text',
                    type='textarea', outlined, dense, readonly, autogrow,
                    input-style='font-size: 12px; font-family: var(--km-font-mono); line-height: 1.5',
                    style='max-height: 250px; overflow-y: auto'
                  )

            template(v-if='currentJob.result.postprocessing')
              template(v-for='(content, key) in currentJob.result.postprocessing', :key='key')
                q-card.q-mb-md(flat, bordered, v-if='content')
                  q-expansion-item(dense, header-class='q-pa-sm', :default-opened='true')
                    template(v-slot:header)
                      .row.items-center.q-gap-4
                        q-icon(:name='resultIcon(String(key))', size='18px', color='grey-7')
                        .km-heading-8 {{ capitalize(String(key)) }}
                    q-card-section
                      q-input(
                        :modelValue='content', type='textarea', outlined, dense, readonly, autogrow,
                        input-style='font-size: 12px; line-height: 1.6',
                        style='max-height: 300px; overflow-y: auto'
                      )

    //- ══ FIXED FOOTER ══════════════════════════════════════════════════
    .col-auto
      q-separator

      //- No job: Run button
      template(v-if='!currentJob')
        .q-pt-sm
          q-btn.full-width(
            color='primary', unelevated, dense, no-caps,
            :disable='!canRun', @click='runPreview', :loading='running',
            icon='play_arrow', :label='m.common_runPipeline()'
          )

      //- Transcribed: Continue button
      template(v-else-if='currentJob?.status === "transcribed"')
        .q-pt-sm
          q-btn.full-width(
            unelevated, dense, color='primary', no-caps,
            :label='m.common_continue()', icon='play_arrow',
            @click='continuePostprocessing', :loading='processingContinue'
          )

      //- Failed: Try again
      template(v-else-if='currentJob?.status === "failed"')
        .q-pt-sm
          q-btn.full-width(
            unelevated, dense, color='primary', no-caps,
            :label='m.common_tryAgain()', icon='refresh',
            @click='resetPreview'
          )
</template>

<script setup lang="ts">
import { ref, computed, watch, onActivated, onDeactivated, onUnmounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import type { PreviewJob } from '@/stores/noteTakerStore'
import { useNotify } from '@/composables/useNotify'

const props = defineProps<{ settingsId: string }>()
const ntStore = useNoteTakerStore()
const { notifyError } = useNotify()

// ── Input state ──
const sourceUrl = ref('')
const selectedFile = ref<File | null>(null)
const newParticipant = ref('')
const participants = ref<string[]>([])
const running = ref(false)

// ── Current job state (persisted in store so it survives navigation) ──
const currentJobId = computed({
  get: () => ntStore.activePreviewJobId,
  set: (val: string | null) => { ntStore.activePreviewJobId = val },
})
const speakerMapping = ref<Record<string, string>>({})
const extraKeytermsInput = ref('')
const meetingNotesInput = ref('')
const processingContinue = ref(false)

// pollingTimer is declared alongside the polling loop below (§B.1).

const previewJobs = computed<PreviewJob[]>(() => ntStore.previewJobs || [])
const currentJob = computed(() => currentJobId.value ? previewJobs.value.find((j) => j.id === currentJobId.value) || null : null)
const canRun = computed(() => Boolean(selectedFile.value) || Boolean(sourceUrl.value.trim()))

const speakerLabels = computed(() => {
  return (currentJob.value?.result?.speaker_labels as string[]) || []
})

// ── Pipeline steps indicator ──
const pipelineSteps = computed(() => {
  const status = currentJob.value?.status || 'pending'
  const hasPostprocessing = Boolean(currentJob.value?.result?.postprocessing)

  const done = 'grey-3'
  const doneText = 'grey-8'
  const active = 'primary'
  const activeText = 'white'
  const pending = 'grey-2'
  const pendingText = 'grey-5'

  const steps = [
    {
      key: 'transcribe',
      label: 'Transcribe',
      icon: ['running', 'pending'].includes(status) ? 'hourglass_top' : 'check_circle',
      color: ['running', 'pending'].includes(status) ? active : done,
      textColor: ['running', 'pending'].includes(status) ? activeText : doneText,
    },
    {
      key: 'review',
      label: 'Review speakers',
      icon: status === 'transcribed' ? 'edit' : (['running', 'pending'].includes(status) ? 'radio_button_unchecked' : 'check_circle'),
      color: status === 'transcribed' ? 'orange' : (hasPostprocessing || status === 'rerunning' ? done : pending),
      textColor: status === 'transcribed' ? 'white' : (hasPostprocessing || status === 'rerunning' ? doneText : pendingText),
    },
    {
      key: 'generate',
      label: 'Generate',
      icon: status === 'rerunning' ? 'hourglass_top' : (status === 'completed' && hasPostprocessing ? 'check_circle' : 'radio_button_unchecked'),
      color: status === 'rerunning' ? active : (status === 'completed' && hasPostprocessing ? done : pending),
      textColor: status === 'rerunning' ? activeText : (status === 'completed' && hasPostprocessing ? doneText : pendingText),
    },
  ]
  if (status === 'failed') {
    return [{ key: 'failed', label: 'Failed', icon: 'error', color: 'negative', textColor: 'white' }]
  }
  return steps
})

const onFileSelected = (e: Event) => {
  selectedFile.value = (e.target as HTMLInputElement).files?.[0] || null
  if (selectedFile.value) sourceUrl.value = ''
}
const fileInput = ref<HTMLInputElement | null>(null)
const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}
const addParticipant = () => {
  const name = newParticipant.value.trim()
  if (name && !participants.value.includes(name)) participants.value.push(name)
  newParticipant.value = ''
}

// ── Run ──
const runPreview = async () => {
  if (!canRun.value) return
  running.value = true
  try {
    const job = await ntStore.runPreview({
      settingsId: props.settingsId,
      sourceUrl: selectedFile.value ? undefined : sourceUrl.value.trim() || undefined,
      file: selectedFile.value || undefined,
      participants: participants.value.length ? [...participants.value] : undefined,
    })
    if (job) {
      ntStore.upsertPreviewJob(job)
      currentJobId.value = job.id
      startPolling()
    }
  } catch (error: any) {
    notifyError(error?.message || 'Failed to start preview')
  } finally { running.value = false }
}

// ── Continue (post-processing) ──
const continuePostprocessing = async () => {
  if (!currentJob.value) return
  processingContinue.value = true
  try {
    await ntStore.rerunPreviewPostprocessing({
      settingsId: props.settingsId,
      jobId: currentJob.value.id,
      speakerMapping: speakerMapping.value,
      extraKeyterms: extraKeytermsInput.value.split(',').map((s) => s.trim()).filter(Boolean),
      meetingNotes: meetingNotesInput.value.trim() || undefined,
    })
    // Update local job status so polling picks it up.
    ntStore.upsertPreviewJob({ ...currentJob.value, status: 'rerunning' })
    stopPolling()
    startPolling()
  } catch (error: any) {
    notifyError(error?.message || 'Post-processing failed')
  } finally { processingContinue.value = false }
}

// ── Reset ──
const resetPreview = () => {
  stopPolling()
  currentJobId.value = null
  speakerMapping.value = {}
  extraKeytermsInput.value = ''
  meetingNotesInput.value = ''
}

// ── Polling (§B.1) ──
// setTimeout-recursive (not setInterval) so one slow request can't pile up
// multiple in-flight copies. `cancelled` guards against late responses after
// onUnmounted / onDeactivated.
let pollingTimer: ReturnType<typeof setTimeout> | null = null
let pollingCancelled = false
const POLL_INTERVAL_MS = 4000
const POLL_MAX_CONSECUTIVE_ERRORS = 3
let pollErrorCount = 0

const pollJob = async () => {
  if (pollingCancelled || !currentJobId.value) return
  try {
    await ntStore.fetchPreviewJobStatus({
      settingsId: props.settingsId,
      jobId: currentJobId.value,
    })
    pollErrorCount = 0
    const job = currentJob.value
    if (job && !['pending', 'running', 'rerunning'].includes(job.status)) {
      stopPolling()
      return
    }
  } catch (err) {
    pollErrorCount += 1
     
    console.warn('[NoteTaker] poll failed', err)
    if (pollErrorCount >= POLL_MAX_CONSECUTIVE_ERRORS) {
      stopPolling()
      return
    }
  }
  if (!pollingCancelled) {
    pollingTimer = setTimeout(pollJob, POLL_INTERVAL_MS)
  }
}
const startPolling = () => {
  pollingCancelled = false
  pollErrorCount = 0
  if (!pollingTimer) pollingTimer = setTimeout(pollJob, POLL_INTERVAL_MS)
}
const stopPolling = () => {
  pollingCancelled = true
  if (pollingTimer) {
    clearTimeout(pollingTimer)
    pollingTimer = null
  }
}

// ── Init speaker mapping + keyterms when transcribed ──
watch(currentJob, (job) => {
  if (job?.status === 'transcribed' && job.result?.speaker_labels) {
    const labels = job.result.speaker_labels as string[]
    const aiMapping = (job.result.speaker_mapping || {}) as Record<string, string>
    speakerMapping.value = Object.fromEntries(
      labels.map((l) => [l, speakerMapping.value[l] || aiMapping[l] || ''])
    )
    const aiKeyterms = (job.result.suggested_keyterms || []) as string[]
    if (aiKeyterms.length && !extraKeytermsInput.value) {
      extraKeytermsInput.value = aiKeyterms.join(', ')
    }
  }
})

// ── Helpers ──
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
const resultIcon = (key: string) => ({ summary: 'summarize', chapters: 'format_list_numbered', insights: 'lightbulb' }[key] || 'article')

// Resume polling when component is re-activated (keep-alive)
onActivated(() => {
  if (currentJobId.value && currentJob.value && ['pending', 'running', 'rerunning'].includes(currentJob.value.status)) {
    startPolling()
  }
})

// Pause polling when navigating away (keep-alive deactivation)
onDeactivated(() => stopPolling())

// Clean up fully when destroyed
onUnmounted(() => stopPolling())
</script>
