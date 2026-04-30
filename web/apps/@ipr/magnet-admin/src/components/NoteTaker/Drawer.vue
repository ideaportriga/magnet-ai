<template>
  <km-drawer-layout storage-key="drawer-note-taker" no-scroll>
    <template #header>
      <div class="cluster full-width">
        <div class="flex-1 km-heading-7">Preview</div>
        <div v-if="currentJob" class="flex-none">
          <km-btn flat dense size="sm" tone="weak" icon="restart_alt" :label="m.common_startOver()" no-caps @click="resetPreview" />
        </div>
      </div>
      <div v-if="!currentJob" class="km-description text-secondary-text">Test your note taker configuration with a recording.</div>
      <km-stepper v-else-if="!isFailed" :steps="stepperSteps" :stepper="stepperIndex" class="preview-stepper" />
    </template>

    <div class="stack full-height full-width" data-gap="0">
      <km-scroll-area class="flex-1 min-h-0">
        <!-- Input form (no active job) -->
        <template v-if="!currentJob">
          <div class="stack preview-body" data-gap="lg">
            <section class="stack" data-gap="sm">
              <div class="cluster" data-gap="xs">
                <km-glyph name="audio_file" size="18px" tone="weak" />
                <div class="km-heading-8">Recording source</div>
              </div>
              <div v-if="selectedFile" class="cluster" data-gap="xs" data-wrap="no">
                <km-chip removable tone="brand" icon="attach" @remove="clearFile">{{ selectedFile.name }}</km-chip>
                <km-btn flat dense round size="sm" icon="swap_horiz" tone="weak" tooltip="Choose another file" @click="fileInput?.click()" />
              </div>
              <div v-else class="cluster" data-gap="xs" data-wrap="no">
                <km-input v-model="sourceUrl" class="flex-1" :placeholder="m.noteTaker_pasteRecordingUrl()" height="32px" clearable />
                <km-btn class="flex-none" flat dense round size="sm" icon="attach" tone="weak" tooltip="Attach file" @click="fileInput?.click()" />
              </div>
              <input ref="fileInput" type="file" hidden accept="audio/*,video/*,.mp4,.mp3,.wav,.m4a,.ogg,.webm,.mkv,.flac" @change="onFileSelected">
            </section>

            <section class="stack" data-gap="sm">
              <div class="cluster" data-gap="xs">
                <km-glyph name="people" size="18px" tone="weak" />
                <div class="km-heading-8">Participants</div>
              </div>
              <div class="km-description text-secondary-text">Optional. Helps with speaker identification.</div>
              <div class="cluster" data-gap="sm">
                <km-input v-model="newParticipant" class="flex-1" :placeholder="m.noteTaker_fullName()" height="32px" @keyup.enter="addParticipant" />
                <km-btn class="flex-none" flat dense round size="sm" icon="add" tone="brand" :disable="!newParticipant.trim()" @click="addParticipant" />
              </div>
              <div v-if="participants.length" class="cluster" data-gap="xs">
                <km-chip v-for="(p, i) in participants" :key="i" removable tone="brand" @remove="participants.splice(i, 1)">{{ p }}</km-chip>
              </div>
            </section>
          </div>
        </template>

        <!-- Job in progress / done -->
        <template v-if="currentJob">
          <div class="stack preview-body" data-gap="md">
            <template v-if="['running', 'pending'].includes(currentJob.status)">
              <div class="cluster preview-loading" data-gap="md">
                <km-loader size="2em" />
                <div class="stack" data-gap="xs">
                  <div class="km-heading-8">Transcribing...</div>
                  <div class="km-description text-secondary-text">This may take a few minutes depending on the recording length.</div>
                </div>
              </div>
            </template>

            <template v-else-if="currentJob.status === 'rerunning'">
              <div class="cluster preview-loading" data-gap="md">
                <km-loader size="2em" />
                <div class="stack" data-gap="xs">
                  <div class="km-heading-8">Generating summary and chapters...</div>
                  <div class="km-description text-secondary-text">Running configured prompt templates.</div>
                </div>
              </div>
            </template>

            <template v-else-if="isFailed">
              <km-banner dense>
                <template #avatar>
                  <km-glyph name="error" tone="danger" />
                </template>
                <div class="stack" data-gap="xs">
                  <div class="km-heading-8">Pipeline failed</div>
                  <div class="km-description preview-error-message">{{ currentJob.result?.error || 'Unknown error' }}</div>
                </div>
              </km-banner>
            </template>

            <template v-else-if="currentJob.status === 'transcribed' && currentJob.result">
              <section class="stack" data-gap="sm">
                <div class="cluster" data-gap="xs">
                  <km-glyph name="file-text" size="18px" tone="weak" />
                  <div class="km-heading-8">Transcript</div>
                </div>
                <km-input
                  :model-value="currentJob.result.full_text || ''"
                  class="font-mono preview-transcript"
                  type="textarea"
                  outlined
                  dense
                  readonly
                  autogrow
                />
              </section>

              <section v-if="speakerLabels.length" class="stack" data-gap="sm">
                <div class="cluster" data-gap="xs">
                  <km-glyph name="people" size="18px" tone="weak" />
                  <div class="km-heading-8">Speaker mapping</div>
                </div>
                <div class="km-description text-secondary-text">Assign real names to detected speakers. Leave empty to keep the label.</div>
                <div class="stack" data-gap="sm">
                  <div v-for="label in speakerLabels" :key="label" class="cluster" data-gap="sm">
                    <km-chip class="flex-none" dense size="sm" shape="square" tone="neutral">{{ label }}</km-chip>
                    <div class="flex-1">
                      <km-input v-model="speakerMapping[label]" :placeholder="m.noteTaker_nameForLabel({ label })" height="32px" />
                    </div>
                  </div>
                </div>
              </section>

              <section class="stack" data-gap="sm">
                <div class="km-heading-8">Additional context</div>
                <div class="stack" data-gap="xs">
                  <div class="km-description text-secondary-text">Key terms (comma-separated)</div>
                  <km-input v-model="extraKeytermsInput" :placeholder="m.noteTaker_productNamesAcronyms()" height="32px" />
                </div>
                <div class="stack" data-gap="xs">
                  <div class="km-description text-secondary-text">Meeting notes (optional)</div>
                  <km-input v-model="meetingNotesInput" :placeholder="m.noteTaker_actionItemsDecisions()" height="60px" />
                </div>
              </section>
            </template>

            <template v-else-if="currentJob.status === 'completed' && currentJob.result">
              <km-card v-if="currentJob.result.full_text" flat bordered>
                <km-expansion-item dense header-class="p-sm" :default-opened="false">
                  <template #header>
                    <div class="cluster" data-gap="xs">
                      <km-glyph name="file-text" size="18px" tone="weak" />
                      <div class="km-heading-8">Transcript</div>
                    </div>
                  </template>
                  <div class="km-card-section">
                    <km-input
                      :model-value="currentJob.result.full_text"
                      class="font-mono preview-transcript"
                      type="textarea"
                      outlined
                      dense
                      readonly
                      autogrow
                    />
                  </div>
                </km-expansion-item>
              </km-card>

              <template v-if="currentJob.result.postprocessing">
                <km-card v-for="(content, key) in currentJob.result.postprocessing" v-show="content" :key="key" flat bordered>
                  <km-expansion-item dense header-class="p-sm" :default-opened="true">
                    <template #header>
                      <div class="cluster" data-gap="xs">
                        <km-glyph :name="resultIcon(String(key))" size="18px" tone="weak" />
                        <div class="km-heading-8">{{ capitalize(String(key)) }}</div>
                      </div>
                    </template>
                    <div class="km-card-section">
                      <km-input
                        :model-value="content"
                        class="preview-postproc"
                        type="textarea"
                        outlined
                        dense
                        readonly
                        autogrow
                      />
                    </div>
                  </km-expansion-item>
                </km-card>
              </template>
            </template>
          </div>
        </template>
      </km-scroll-area>

      <div class="flex-none preview-footer">
        <km-separator />
        <template v-if="!currentJob">
          <km-btn class="full-width" unelevated dense no-caps :disable="!canRun" :loading="running" icon="play" :label="m.common_runPipeline()" @click="runPreview" />
        </template>
        <template v-else-if="currentJob?.status === 'transcribed'">
          <km-btn class="full-width" unelevated dense no-caps :label="m.common_continue()" icon="play" :loading="processingContinue" @click="continuePostprocessing" />
        </template>
        <template v-else-if="isFailed">
          <km-btn class="full-width" unelevated dense no-caps :label="m.common_tryAgain()" icon="refresh" @click="resetPreview" />
        </template>
      </div>
    </div>
  </km-drawer-layout>
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

const previewJobs = computed<PreviewJob[]>(() => ntStore.previewJobs || [])
const currentJob = computed(() => currentJobId.value ? previewJobs.value.find((j) => j.id === currentJobId.value) || null : null)
const canRun = computed(() => Boolean(selectedFile.value) || Boolean(sourceUrl.value.trim()))
const isFailed = computed(() => currentJob.value?.status === 'failed')

const speakerLabels = computed(() => {
  return (currentJob.value?.result?.speaker_labels as string[]) || []
})

// ── Pipeline stepper ──
// `KmStepper` auto-picks edit/check/circle indicator icons by comparing each
// step index against the active `stepper` index (done/active/todo).
const stepperSteps: Array<{ label: string }> = [
  { label: 'Transcribe' },
  { label: 'Review speakers' },
  { label: 'Generate' },
]

const stepperIndex = computed(() => {
  const status = currentJob.value?.status || 'pending'
  if (['running', 'pending'].includes(status)) return 0
  if (status === 'transcribed') return 1
  if (status === 'rerunning') return 2
  if (status === 'completed') return stepperSteps.length // all done
  return 0
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

<style scoped>
.preview-stepper {
  padding-block-start: var(--ds-space-sm);
}

.preview-body {
  padding-block: var(--ds-space-md);
  padding-inline-end: var(--ds-space-xs);
}

.preview-loading {
  padding-block: var(--ds-space-xl);
  padding-inline: var(--ds-space-md);
}

.preview-footer {
  padding-block-start: var(--ds-space-sm);
}

.preview-error-message {
  overflow-wrap: break-word;
}

.preview-transcript :deep(textarea) {
  font-size: 12px;
  line-height: 1.5;
  max-block-size: 250px;
  overflow-block: auto;
}

.preview-postproc :deep(textarea) {
  font-size: 12px;
  line-height: 1.6;
  max-block-size: 300px;
  overflow-block: auto;
}
</style>
