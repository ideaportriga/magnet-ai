<template>
  <kg-dialog-source-base
    :show-dialog="dialogOpen"
    :source="props.source || null"
    :title="isEditMode ? 'Edit Web Source' : 'Connect Web Source'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Connect'"
    :loading="loading"
    :disable-confirm="loading || !isFormValid"
    :error="error"
    size="md"
    syncable
    @update:show-dialog="(v: boolean) => emit('update:showDialog', v)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
    @changed="clearError"
  >
    <kg-dialog-section title="URL" description="Enter the URL to scrape." icon="link">
      <km-input
        ref="urlRef"
        v-model="url"
        height="36px"
        placeholder="https://example.com/docs"
        :rules="urlRules"
        required
      />
    </kg-dialog-section>

    <kg-dialog-section title="Crawl Options" description="Configure how the web scraper discovers and extracts content." icon="settings">
      <kg-toggle-field
        v-model="followLinks"
        title="Follow Links"
        description="Automatically discover and scrape linked pages within the same domain"
      />

      <template v-if="followLinks">
        <div class="q-mt-md q-mb-md">
          <div class="km-input-label q-pb-xs">Max Depth</div>
          <km-input
            v-model="maxDepth"
            height="36px"
            type="number"
            placeholder="2"
            :rules="[(v: string) => (Number(v) >= 1 && Number(v) <= 10) || 'Must be between 1 and 10']"
          />
          <div class="text-grey-7 text-caption q-mt-xs">How many levels of links to follow from the seed URL</div>
        </div>

        <div class="q-mb-md">
          <div class="km-input-label q-pb-xs">Max Pages</div>
          <km-input
            v-model="maxPages"
            height="36px"
            type="number"
            placeholder="100"
            :rules="[(v: string) => (Number(v) >= 1 && Number(v) <= 1000) || 'Must be between 1 and 1000']"
          />
          <div class="text-grey-7 text-caption q-mt-xs">Maximum number of pages to scrape</div>
        </div>
      </template>

      <div class="q-mt-md">
        <div class="km-input-label q-pb-xs">CSS Selector (optional)</div>
        <km-input
          v-model="cssSelector"
          height="36px"
          placeholder="main, article, .content"
        />
        <div class="text-grey-7 text-caption q-mt-xs">Target specific page elements for content extraction. Leave empty to auto-detect.</div>
      </div>
    </kg-dialog-section>
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDialogSection, KgDialogSourceBase, KgToggleField, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

type WebSourceConfig = {
  url?: string
  follow_links?: boolean
  max_depth?: number
  max_pages?: number
  css_selector?: string | null
}

type WebSourceRecord = Omit<SourceRow, 'type' | 'config'> & {
  type: 'web'
  config?: WebSourceConfig | null
}

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: WebSourceRecord | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'created', result: any): void
  (e: 'update:showDialog', value: boolean): void
}>()

const store = useStore()
const $q = useQuasar()
const url = ref('')
const followLinks = ref(false)
const maxDepth = ref('2')
const maxPages = ref('100')
const cssSelector = ref('')
const loading = ref(false)
const error = ref('')

const urlRef = ref<any>(null)

const urlRules = [
  (val: string) => !!(val && val.trim()) || 'URL is required',
  (val: string) => /^https?:\/\//.test(val || '') || 'Must start with http(s)://',
]

const isFormValid = computed(() => !!url.value.trim() && /^https?:\/\//.test(url.value))

const isEditMode = computed(() => !!props.source)
const dialogOpen = computed(() => props.showDialog)

watch(
  () => [props.showDialog, props.source] as const,
  () => {
    if (props.showDialog) {
      if (props.source) {
        try {
          const cfg = (props.source?.config || {}) as WebSourceConfig
          url.value = cfg.url || ''
          followLinks.value = !!cfg.follow_links
          maxDepth.value = String(cfg.max_depth ?? 2)
          maxPages.value = String(cfg.max_pages ?? 100)
          cssSelector.value = cfg.css_selector || ''
        } catch {
          // ignore prefill errors
        }
      } else {
        url.value = ''
        followLinks.value = false
        maxDepth.value = '2'
        maxPages.value = '100'
        cssSelector.value = ''
      }
    }
  },
  { immediate: true }
)

function buildConfig(): WebSourceConfig {
  const config: WebSourceConfig = { url: url.value.trim() }
  config.follow_links = followLinks.value
  if (followLinks.value) {
    config.max_depth = Number(maxDepth.value) || 2
    config.max_pages = Number(maxPages.value) || 100
  }
  if (cssSelector.value.trim()) {
    config.css_selector = cssSelector.value.trim()
  }
  return config
}

function buildCron(schedule: ScheduleFormState) {
  if (schedule.interval === 'none') return null
  if (schedule.interval === 'hourly') return { minute: 0, hour: '*' }
  if (schedule.interval === 'daily') return { minute: 0, hour: schedule.hour }
  return { minute: 0, hour: schedule.hour, day_of_week: schedule.day }
}

async function applySchedule(sourceId: string, schedule: ScheduleFormState) {
  const shouldCall = schedule.interval !== 'none' || (props.source?.schedule !== null && props.source?.schedule !== undefined)
  if (!shouldCall) return

  const endpoint = store.getters.config.api.aiBridge.urlAdmin
  const payload: any = { interval: schedule.interval }
  if (schedule.interval !== 'none') {
    payload.timezone = schedule.timezone
    payload.cron = buildCron(schedule)
  }

  const response = await fetchData({
    endpoint,
    service: `knowledge_graphs/${props.graphId}/sources/${sourceId}/schedule_sync`,
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })

  if (response.ok) return

  let msg = 'Failed to update sync schedule'
  try {
    const err = await response.json()
    msg = err?.detail || err?.error || msg
  } catch {
    // ignore parse errors
  }
  throw new Error(msg)
}

const clearError = () => {
  if (error.value) error.value = ''
}

const addSource = async (sourceName: string, schedule: ScheduleFormState) => {
  const urlOk = await (urlRef.value?.validate?.() ?? true)
  if (!urlOk) return

  loading.value = true
  error.value = ''

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const payload = {
      type: 'web',
      name: sourceName.trim() || null,
      config: buildConfig(),
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources`,
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.ok) {
      const result = await response.json()
      if (schedule.interval !== 'none') {
        try {
          await applySchedule(result.id, schedule)
        } catch (e: any) {
          $q.notify({
            type: 'negative',
            message: e?.message || 'Source created, but schedule could not be saved',
            position: 'top',
          })
        }
      }
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to create web source'
    }
  } catch (err) {
    console.error('Web source creation error:', err)
    error.value = 'Failed to create web source. Please try again.'
  } finally {
    loading.value = false
  }
}

const updateSource = async (sourceName: string, schedule: ScheduleFormState) => {
  if (!props.source) return
  const urlOk = await (urlRef.value?.validate?.() ?? true)
  if (!urlOk) return
  loading.value = true
  error.value = ''
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name: sourceName.trim() || null,
      config: buildConfig(),
    }
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${props.source.id}`,
      method: 'PATCH',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
    if (response.ok) {
      const result = await response.json()
      await applySchedule(props.source.id, schedule)
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to save web source'
    }
  } catch (err) {
    console.error('Web source update error:', err)
    error.value = 'Failed to save web source. Please try again.'
  } finally {
    loading.value = false
  }
}

const onConfirm = async (payload: { sourceName: string; schedule: ScheduleFormState }) => {
  if (isEditMode.value) {
    await updateSource(payload.sourceName, payload.schedule)
  } else {
    await addSource(payload.sourceName, payload.schedule)
  }
}

watch([url, followLinks, maxDepth, maxPages, cssSelector], () => {
  if (error.value) error.value = ''
})
</script>
