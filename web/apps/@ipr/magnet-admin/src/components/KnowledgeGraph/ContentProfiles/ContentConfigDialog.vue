<template>
  <q-dialog v-model="dialogOpen" :persistent="!isReadonlyProfile && isDirty">
    <q-card class="q-px-lg q-py-sm" style="min-width: 800px; max-width: 800px; height: 820px; display: flex; flex-direction: column">
      <q-card-section>
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">{{ dialogTitle }}</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="cancel" />
          </div>
        </div>
      </q-card-section>

      <q-card-section class="dialog-body">
        <q-form @submit="save">
          <div class="q-mb-lg">
            <div class="row q-col-gutter-lg">
              <!-- Name -->
              <div class="col-6">
                <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Name</div>
                <div class="km-description text-secondary-text q-mt-xs q-mb-md">Set profile name for this content configuration.</div>
                <km-input ref="nameRef" v-model="form.name" :rules="nameRules" :readonly="isLockedNativeProfile || isReadonlyProfile" required />
              </div>

              <!-- Content Reader -->
              <div class="col-6">
                <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Content Reader</div>
                <div class="km-description text-secondary-text q-mt-xs q-mb-md">Select tool used to read the content.</div>
                <km-select
                  v-model="form.reader.name"
                  :options="isLockedNativeProfile || isReadonlyProfile ? readerOptions : selectableReaderOptions"
                  :disable="isLockedNativeProfile || isReadonlyProfile"
                  emit-value
                  map-options
                />
              </div>
            </div>
          </div>

          <div class="q-mb-lg">
            <!-- Content Matching -->
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Content Matching</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-sm">
              Choose which content this profile should apply to by editing the highlighted parts below.
            </div>
            <div class="content-matching-sentence q-mt-md">
              <template v-if="isReadonlyProfile">
                <span>This built-in profile is automatically used only when no other content profile matches.</span>
              </template>
              <template v-else-if="isLockedNativeProfile">
                <span>This profile automatically applies to all Fluid Topics sources.</span>
              </template>
              <template v-else>
                <span>Apply this profile matching</span>
                <kg-inline-field tooltip="Glob pattern (e.g. *.pdf). Separate multiple patterns with commas. Leave empty to match all.">
                  <input
                    v-model="form.glob_pattern"
                    class="kg-inline-field__input"
                    placeholder="any file"
                    spellcheck="false"
                    :style="{ width: patternInputWidth }"
                  >
                </kg-inline-field>
                <span>pattern from</span>
                <source-tree-dropdown v-model="sourceIdsModel" :sources="sources || []" />
              </template>
            </div>
          </div>

          <div class="q-mb-lg">
            <!-- Chunking Strategy -->
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Chunking Strategy</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-md">
              {{
                isReadonlyProfile
                  ? 'This built-in fallback always uses the Plain Text Reader and keeps the content as a single chunk up to the maximum size.'
                  : isLockedNativeProfile
                    ? 'Structured Fluid Topics content is already chunked upstream, so this reader always uses the built-in pre-chunked flow.'
                    : 'Select the strategy used to split content into chunks.'
              }}
            </div>
            <div class="row q-col-gutter-lg items-center">
              <div class="col-4">
                <km-select
                  v-model="form.chunker.strategy"
                  :options="chunkingStrategyOptions"
                  emit-value
                  map-options
                  :disable="isLockedNativeProfile || isReadonlyProfile"
                />
              </div>
              <div class="col-8">
                <div class="km-description">{{ selectedChunkingStrategyDescription }}</div>
              </div>
            </div>
            <div
              v-if="!isLockedNativeProfile && !isReadonlyProfile && isLLMStrategy"
              class="km-description q-mt-lg row items-center q-gap-8 q-pa-md rounded-borders bg-yellow-1 text-yellow-10"
              style="border: 1px solid var(--q-warning)"
            >
              <q-icon name="warning" color="yellow-8" size="26px" />
              <div class="col">LLM-based chunking may incur significant costs and can run for a long time, especially on large documents.</div>
            </div>
          </div>

          <template v-if="!isLockedNativeProfile && !isReadonlyProfile && isLLMStrategy">
            <div class="q-mb-lg">
              <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Chunking Prompt</div>
              <div class="km-description text-secondary-text q-mt-xs q-mb-md">Select a prompt template to use for chunking.</div>
              <div class="row q-gap-8">
                <div class="col-grow">
                  <km-select
                    ref="promptTemplateRef"
                    v-model="form.chunker.options.prompt_template_system_name"
                    placeholder="Select a prompt template"
                    class="col-grow"
                    :options="templateOptions"
                    :loading="loadingTemplates"
                    :rules="[required()]"
                    required
                    has-dropdown-search
                    emit-value
                    map-options
                    option-value="system_name"
                    option-label="name"
                  />
                </div>
                <km-btn
                  flat
                  icon="fa fa-external-link"
                  color="secondary-text"
                  :disable="!form.chunker.options.prompt_template_system_name"
                  label-class="km-button-text"
                  icon-size="16px"
                  @click="openPromptTemplateInNewTab"
                />
              </div>
            </div>
          </template>

          <template v-if="!isLockedNativeProfile && !isReadonlyProfile && isLLMStrategy">
            <div class="q-mb-lg">
              <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Handling Content Size</div>
              <div class="km-description text-secondary-text q-mt-xs q-mb-md">
                LLMs have limited context window, so content must be divided into smaller segments before executing LLM-based chunking. The
                <b>Segment Overlap</b>
                parameter controls content repetition between consecutive segments. The
                <b>Last Segment Allowed Expansion</b>
                parameter allows the final segment to be expanded beyond the normal segment size to reduce small trailing remainders.
              </div>

              <div class="row q-col-gutter-lg q-mb-lg">
                <div class="col-4">
                  <div class="km-input-label q-pb-sm">Segment Size (characters)</div>
                  <km-input v-model.number="form.chunker.options.llm_batch_size" type="number" min="100" />
                </div>
                <div class="col-4">
                  <div class="km-input-label q-pb-sm">Segment Overlap (%)</div>
                  <div class="row items-center" style="height: 36px">
                    <q-slider
                      v-model="form.chunker.options.llm_batch_overlap"
                      :min="0"
                      :max="0.9"
                      :step="0.02"
                      label
                      :label-value="`${Math.round((form.chunker.options.llm_batch_overlap || 0) * 100)}%`"
                    />
                  </div>
                </div>
                <div class="col-4">
                  <div class="km-input-label q-pb-sm">Last Segment Allowed Expansion (%)</div>
                  <div class="row items-center q-pr-sm" style="height: 36px">
                    <q-slider
                      v-model="form.chunker.options.llm_last_segment_increase"
                      :min="0"
                      :max="1"
                      :step="0.02"
                      label
                      :label-value="`${Math.round((form.chunker.options.llm_last_segment_increase || 0) * 100)}%`"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>

          <template v-if="!isLockedNativeProfile && !isReadonlyProfile && isRecursiveStrategy">
            <div class="q-mb-lg">
              <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Chunking Settings</div>
              <div class="km-description text-secondary-text q-mt-xs q-mb-md">
                Adjust how content is divided into chunks when using the recursive character text splitting strategy.
                <b>Splitters</b>
                control where content is split into smaller parts; each splitter is tried in order of priority, until content fits into the chunk max
                size.
                <b>Chunk Overlap</b>
                allows a portion of content to be repeated between consecutive chunks to provide better context continuity.
              </div>

              <div class="row q-col-gutter-lg">
                <div class="col-8">
                  <div class="km-input-label q-pb-xs">Splitters</div>
                  <div class="splitters-container q-py-xs" style="border: 1px solid var(--q-border); border-radius: var(--radius-sm)">
                    <div class="row items-center q-gutter-xs">
                      <q-chip
                        v-for="(splitter, index) in form.chunker.options.splitters"
                        :key="index"
                        removable
                        color="primary-light"
                        text-color="primary"
                        square
                        size="12px"
                        @remove="removeSplitter(index)"
                      >
                        {{ formatSplitterDisplay(splitter) }}
                      </q-chip>
                      <template v-if="showNewSplitterInput">
                        <km-input
                          ref="newSplitterInput"
                          v-model="newSplitter"
                          placeholder="Add (Enter)"
                          dense
                          style="width: 160px"
                          @keyup.enter="addSplitter"
                          @keyup.esc.stop.prevent="cancelAddSplitter"
                          @blur="cancelAddSplitter"
                        />
                      </template>
                      <template v-else>
                        <q-btn
                          dense
                          flat
                          color="primary-light"
                          text-color="primary"
                          icon="add"
                          class="q-ml-sm q-my-none q-pa-none"
                          style="height: 24px; width: 28px; border-radius: var(--radius-sm)"
                          @click="showAddInput"
                        />
                      </template>
                    </div>
                  </div>
                  <div class="km-description text-secondary-text">
                    Enter separators in order of priority. Use keywords:
                    <i>space</i>
                    ,
                    <i>tab</i>
                    ,
                    <i>newline</i>
                    ,
                    <i>empty</i>
                    or escape sequences (\n, \t, ...).
                  </div>
                </div>
                <div class="col-4">
                  <div class="km-input-label q-pb-xs">Chunk Overlap (%)</div>
                  <div class="row items-center q-pr-sm" style="height: 36px">
                    <q-slider
                      v-model="form.chunker.options.recursive_chunk_overlap"
                      :min="0"
                      :max="0.9"
                      :step="0.02"
                      label
                      :label-value="`${Math.round((form.chunker.options.recursive_chunk_overlap || 0) * 100)}%`"
                    />
                  </div>
                  <div class="km-description text-secondary-text q-mt-xs">Percentage of chunk max size.</div>
                </div>
              </div>
            </div>
          </template>

          <!-- Document Level Settings -->
          <div class="q-mb-lg">
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Document Level Settings</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-md">
              These settings apply to the produced document as a whole. Use it to configure document-level information.
            </div>
            <div>
              <div class="km-input-label q-pb-xs">Document Title</div>
              <km-input v-model="form.chunker.options.document_title_pattern" :readonly="isReadonlyProfile" placeholder="e.g., {title} — {filename}">
                <template #append>
                  <q-icon name="info" size="18px" class="q-ml-xs text-secondary cursor-pointer" />
                  <q-tooltip anchor="top middle" self="bottom middle" class="q-ml-sm q-pa-sm" max-width="350px">
                    <div class="km-description">
                      <div class="q-mb-xs text-weight-bold">Available variables:</div>
                      <ul class="q-ml-md q-mb-none" style="padding-left: 16px">
                        <li>
                          <b>{filename}</b>
                          : Source file name
                        </li>
                        <li>
                          <b>{title}</b>
                          : Original document title (if available)
                        </li>
                        <li>
                          <b>{date}</b>
                          : Document date
                        </li>
                        <li>
                          <b>{source}</b>
                          : Data source name
                        </li>
                      </ul>
                    </div>
                  </q-tooltip>
                </template>
              </km-input>
            </div>
          </div>

          <!-- Chunk Level Settings -->
          <div class="q-mb-lg">
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Chunk Level Settings</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-md">
              These settings apply to each chunk produced by the chunker. Use it to configure chunk-level information.
            </div>
            <div class="row q-col-gutter-lg q-mb-md">
              <div class="col-8">
                <div class="km-input-label q-pb-xs">Chunk Title</div>
                <km-input
                  v-model="form.chunker.options.chunk_title_pattern"
                  :readonly="isReadonlyProfile"
                  placeholder="e.g., Chunk {index} — Page {page}"
                >
                  <template #append>
                    <q-icon name="info" size="18px" class="q-ml-xs text-secondary cursor-pointer" />
                    <q-tooltip anchor="top middle" self="bottom middle" class="q-ml-sm q-pa-sm" max-width="350px">
                      <div class="km-description">
                        <div class="q-mb-xs text-weight-bold">Available variables:</div>
                        <ul class="q-ml-md q-mb-none" style="padding-left: 16px">
                          <li>
                            <b>{index}</b>
                            : Chunk number
                          </li>
                          <li>
                            <b>{page}</b>
                            : Page number (if available)
                          </li>
                          <li>
                            <b>{filename}</b>
                            : Source file name
                          </li>
                          <li>
                            <b>{title}</b>
                            : Document title
                          </li>
                          <li>
                            <b>{date}</b>
                            : Document date
                          </li>
                          <li>
                            <b>{source}</b>
                            : Data source name
                          </li>
                        </ul>
                      </div>
                    </q-tooltip>
                  </template>
                </km-input>
              </div>
              <div class="col-4">
                <div class="km-input-label q-pb-xs">Chunk Max Size (characters)</div>
                <km-input v-model.number="form.chunker.options.chunk_max_size" :readonly="isReadonlyProfile" type="number" min="100" required />
              </div>
            </div>
          </div>
        </q-form>
      </q-card-section>

      <q-card-actions class="q-py-lg q-pr-lg">
        <km-btn :label="dismissLabel" flat color="primary" @click="cancel" />
        <q-space v-if="!isReadonlyProfile" />
        <km-btn v-if="!isReadonlyProfile" :label="m.common_save()" @click="save" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import router from '@/router'
import { m } from '@/paraglide/messages'
import { fetchData } from '@shared'
import { required } from '@/utils/validationRules'
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import KgInlineField from '../common/KgInlineField.vue'
import type { SourceRow } from '../Sources/models'
import type { ContentConfigRow } from './models'
import {
  chunkingStrategyOptions,
  FLUID_TOPICS_NATIVE_PROFILE_NAME,
  FLUID_TOPICS_SOURCE_TYPE,
  FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY,
  FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE,
  FLUID_TOPICS_STRUCTURED_READER,
  hasDuplicateContentProfileName,
  hasReservedFluidTopicsNativeProfileName,
  hasReservedVirtualFallbackProfileName,
  isLockedFluidTopicsNativeProfile,
  isVirtualFallbackContentProfile,
  readerOptions,
  selectableReaderOptions,
  SHAREPOINT_PAGE_PROMPT_TEMPLATE_SYSTEM_NAME,
  SHAREPOINT_PAGE_READER,
  SHAREPOINT_SOURCE_TYPE,
  VIRTUAL_FALLBACK_PROFILE_NAME,
} from './models'
import SourceTreeDropdown from './SourceTreeDropdown.vue'

const props = defineProps<{
  showDialog: boolean
  config?: ContentConfigRow
  sources?: SourceRow[]
  existingConfigs?: ContentConfigRow[]
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'save', value: any): void
  (e: 'cancel'): void
}>()

const dialogOpen = computed({
  get: () => props.showDialog,
  set: (value) => emit('update:showDialog', value),
})
const isEditing = ref(false)

// Prompt template options (loaded from admin API)
const templateOptions = ref<any[]>([])
const loadingTemplates = ref(false)
const appStore = useAppStore()
const { notifyError } = useNotify()

const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: 'prompt_templates',
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      const data = await response.json()
      templateOptions.value = data.items
    }
  } catch (error) {

    notifyError(m.knowledgeGraph_failedToLoadPromptTemplates())
  } finally {
    loadingTemplates.value = false
  }
}

// Source selection helpers
const ALL_SOURCES_KEY = '__ALL__'
const NONE_SELECTED_KEY = '__NONE__'
const groupKey = (type: string) => `__GROUP__${type}`
const FLUID_TOPICS_GROUP_KEY = groupKey(FLUID_TOPICS_SOURCE_TYPE)
const SHAREPOINT_GROUP_KEY = groupKey(SHAREPOINT_SOURCE_TYPE)
const mapLegacySourceTypesToSelectors = (legacyTypes: string[]) => {
  const typeSet = new Set((legacyTypes || []).map((t) => String(t)).filter(Boolean))
  return [...typeSet].map((type) => groupKey(type))
}

const applyLockedNativeProfileConstraints = (target: ReturnType<typeof getDefaultForm>) => {
  target.name = FLUID_TOPICS_NATIVE_PROFILE_NAME
  target.enabled = true
  target.glob_pattern = ''
  target.reader.name = FLUID_TOPICS_STRUCTURED_READER
  target.reader.options = {
    ...(target.reader.options || {}),
    [FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY]: FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE,
  }
  target.chunker.strategy = 'none'
  target.source_ids = [FLUID_TOPICS_GROUP_KEY]
}

const applyReadonlyFallbackConstraints = (target: ReturnType<typeof getDefaultForm>) => {
  target.name = VIRTUAL_FALLBACK_PROFILE_NAME
  target.enabled = true
  target.glob_pattern = ''
  target.source_ids = []
  target.reader = {
    name: 'plain_text',
    options: {},
  }
  target.chunker = {
    strategy: 'none',
    options: {
      llm_batch_size: 15000,
      llm_batch_overlap: 0.1,
      llm_last_segment_increase: 0,
      recursive_chunk_size: 15000,
      recursive_chunk_overlap: 0.1,
      chunk_max_size: 15000,
      splitters: ['\n\n', '\n', ' ', ''],
      prompt_template_system_name: '',
      document_title_pattern: '',
      chunk_title_pattern: '',
    },
  }
}

const applySharePointPageDefaults = (target: ReturnType<typeof getDefaultForm>) => {
  if (!String(target.glob_pattern || '').trim()) {
    target.glob_pattern = '*.aspx'
  }

  if (!Array.isArray(target.source_ids) || target.source_ids.length === 0 || target.source_ids.includes(NONE_SELECTED_KEY)) {
    target.source_ids = [SHAREPOINT_GROUP_KEY]
  }

  if (!target.chunker?.strategy || target.chunker.strategy === 'recursive_character_text_splitting' || target.chunker.strategy === 'none') {
    target.chunker.strategy = 'llm'
  }

  if (!String(target.chunker?.options?.prompt_template_system_name || '').trim()) {
    target.chunker.options.prompt_template_system_name = SHAREPOINT_PAGE_PROMPT_TEMPLATE_SYSTEM_NAME
  }
}

// Bridge UI ↔ stored semantics:
// - UI uses __ALL__, __GROUP__type, __NONE__, or individual IDs
// - stored `source_ids: []` means "all sources" (backwards compatible)
// - stored `source_ids: ['__NONE__']` means explicitly no sources
// - stored `source_ids: ['__GROUP__type', ...]` means type groups
// - stored `source_ids: [ids...]` means specific sources
// Items are independent - no auto-collapsing of individual sources into groups.
// Group selectors are stored as virtual markers so future sources of that type
// inherit the selection automatically.
const sourceIdsModel = computed<string[]>({
  get: () => {
    const stored = Array.isArray(form.value.source_ids) ? form.value.source_ids : []

    // Explicit "none" marker
    if (stored.includes(NONE_SELECTED_KEY)) {
      return []
    }

    // Empty = all sources (backwards compatible)
    if (stored.length === 0) {
      return [ALL_SOURCES_KEY]
    }

    // Return stored values as-is (group keys and individual IDs are stored directly)
    return stored
  },
  set: (uiValue) => {
    const incoming = Array.isArray(uiValue) ? uiValue.filter(Boolean) : []

    // __ALL__ = store empty array (backwards compatible)
    if (incoming.includes(ALL_SOURCES_KEY)) {
      form.value.source_ids = []
      return
    }

    // Empty selection = store explicit "none" marker
    if (incoming.length === 0) {
      form.value.source_ids = [NONE_SELECTED_KEY]
      return
    }

    // Store selectors as-is (group keys remain virtual; source IDs stay explicit)
    form.value.source_ids = [...new Set(incoming)]
  },
})

const patternInputWidth = computed(() => {
  const value = form.value.glob_pattern || ''
  if (!value) {
    return '8ch'
  }
  return `${value.length + 1}ch`
})

const getDefaultForm = () => ({
  name: '',
  enabled: true,
  glob_pattern: '',
  source_ids: [] as string[],
  reader: {
    name: 'plain_text',
    options: {},
  },
  chunker: {
    strategy: 'recursive_character_text_splitting',
    options: {
      // LLM strategy batching
      llm_batch_size: 18000,
      llm_batch_overlap: 0.1,
      llm_last_segment_increase: 0,
      // Recursive strategy chunk sizing
      recursive_chunk_size: 18000,
      recursive_chunk_overlap: 0.1,
      // Chunk-level constraints (applies to all strategies)
      chunk_max_size: 18000,
      splitters: ['\n\n', '\n', ' ', ''],
      prompt_template_system_name: '',
      // Optional pattern for document title generation
      document_title_pattern: '',
      // Optional pattern for chunk title generation
      chunk_title_pattern: '',
    },
  },
})

const form = ref(getDefaultForm())
const initialFormState = ref(getDefaultForm())
const nameRef = ref()
const promptTemplateRef = ref()
const newSplitter = ref('')
const showNewSplitterInput = ref(false)
const newSplitterInput = ref()
const isHydratingForm = ref(false)
const isReadonlyProfile = computed(() => isEditing.value && isVirtualFallbackContentProfile(props.config ?? form.value))
const dialogTitle = computed(() => (isReadonlyProfile.value ? 'View Content Profile' : `${isEditing.value ? 'Edit' : 'Add'} Content Profile`))
const dismissLabel = computed(() => (isReadonlyProfile.value ? 'Close' : 'Cancel'))
const isLockedNativeProfile = computed(() => isEditing.value && isLockedFluidTopicsNativeProfile(props.config ?? form.value))
const isSharePointPageReader = computed(() => form.value.reader.name === SHAREPOINT_PAGE_READER)
const isLLMStrategy = computed(() => form.value.chunker.strategy === 'llm')
const isRecursiveStrategy = computed(() => form.value.chunker.strategy === 'recursive_character_text_splitting')
const isDirty = computed(() => JSON.stringify(form.value) !== JSON.stringify(initialFormState.value))
const selectedChunkingStrategyDescription = computed(() => {
  if (isReadonlyProfile.value) {
    return 'This fallback profile stores the content as a single plain-text chunk and truncates only if it exceeds the maximum size.'
  }

  if (isLockedNativeProfile.value) {
    return 'This reader keeps upstream Fluid Topics chunk boundaries and skips strategy-driven splitting.'
  }

  const option = chunkingStrategyOptions.find((o) => o.value === form.value.chunker.strategy)
  return option?.description || ''
})

const validateReservedProfileName = (value: string) => {
  if (isLockedNativeProfile.value || isReadonlyProfile.value) {
    return true
  }

  if (hasReservedFluidTopicsNativeProfileName(value)) {
    return 'This name is reserved for the Fluid Topics native profile.'
  }

  if (hasReservedVirtualFallbackProfileName(value)) {
    return 'This name is reserved for the built-in fallback content profile.'
  }

  return true
}

const validateDuplicateProfileName = (value: string) => {
  if (isLockedNativeProfile.value || isReadonlyProfile.value) {
    return true
  }

  if (!String(value || '').trim()) {
    return true
  }

  return hasDuplicateContentProfileName(value, props.existingConfigs || [], props.config?.name)
    ? 'A content profile with this name already exists.'
    : true
}

const nameRules = [required(), validateReservedProfileName, validateDuplicateProfileName]

// Splitter management functions
const formatSplitterDisplay = (splitter: string): string => {
  if (splitter === '\n\n') return '\\n\\n'
  if (splitter === '\n') return '\\n'
  if (splitter === '\t') return '\\t'
  if (splitter === ' ') return 'space'
  if (splitter === '') return 'empty'
  return splitter
}

const parseSplitterInput = (input: string): string => {
  // Replace escape sequences with actual characters
  const trimmed = input.trim().toLowerCase()
  if (trimmed === 'space') return ' '
  if (trimmed === 'tab') return '\t'
  if (trimmed === 'newline' || trimmed === 'enter' || trimmed === 'linebreak') return '\n'
  if (trimmed === 'empty' || trimmed === 'none') return ''
  return input.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\r/g, '\r')
}

const addSplitter = () => {
  if (newSplitter.value !== '') {
    const parsed = parseSplitterInput(newSplitter.value)
    if (!form.value.chunker.options.splitters.includes(parsed)) {
      form.value.chunker.options.splitters.push(parsed)
    }
    newSplitter.value = ''
    showNewSplitterInput.value = false
  }
}

const removeSplitter = (index: number) => {
  form.value.chunker.options.splitters.splice(index, 1)
}

const showAddInput = () => {
  showNewSplitterInput.value = true
  requestAnimationFrame(() => {
    // focus the input after it renders
    ;(newSplitterInput.value as any)?.focus?.()
  })
}

const cancelAddSplitter = () => {
  newSplitter.value = ''
  showNewSplitterInput.value = false
}

const initForm = () => {
  isHydratingForm.value = true
  if (props.config) {
    isEditing.value = true

    // Parse chunker config
    const chunkerStrategy = props.config.chunker?.strategy || 'recursive_character_text_splitting'
    const chunkerOptions = props.config.chunker?.options || {}
    const normalizedOptions: any = {
      llm_batch_size: chunkerOptions.llm_batch_size ?? chunkerOptions.batch_size ?? 18000,
      llm_batch_overlap: chunkerOptions.llm_batch_overlap ?? chunkerOptions.batch_overlap ?? 0.1,
      llm_last_segment_increase: typeof chunkerOptions.llm_last_segment_increase !== 'undefined' ? chunkerOptions.llm_last_segment_increase : 0,
      chunk_max_size:
        typeof chunkerOptions.chunk_max_size !== 'undefined'
          ? chunkerOptions.chunk_max_size
          : (chunkerOptions.recursive_chunk_size ?? chunkerOptions.llm_batch_size ?? 18000),
      // prefer new recursive_*; fall back to legacy rc_* and old batch_* keys
      recursive_chunk_size: chunkerOptions.recursive_chunk_size ?? chunkerOptions.rc_chunk_size ?? chunkerOptions.batch_size ?? 18000,
      recursive_chunk_overlap: chunkerOptions.recursive_chunk_overlap ?? chunkerOptions.rc_chunk_overlap ?? chunkerOptions.batch_overlap ?? 0.1,
      splitters: chunkerOptions.splitters || ['\n\n', '\n', ' ', ''],
      prompt_template_system_name: chunkerOptions.prompt_template_system_name,
      document_title_pattern: chunkerOptions.document_title_pattern || '',
      chunk_title_pattern: chunkerOptions.chunk_title_pattern || '',
    }

    // Backward compatibility:
    // - prefer explicit source_ids
    // - if only legacy source_types exist, map them to current sources (best-effort)
    let initialSourceIds: string[] = []
    if (Array.isArray(props.config.source_ids)) {
      initialSourceIds = props.config.source_ids
    } else if (Array.isArray(props.config.source_types) && props.config.source_types.length > 0) {
      initialSourceIds = mapLegacySourceTypesToSelectors(props.config.source_types)
    }

    form.value = {
      name: props.config.name || '',
      enabled: props.config.enabled ?? true,
      glob_pattern: props.config.glob_pattern || '',
      source_ids: initialSourceIds,
      reader: {
        name: props.config.reader?.name || 'plain_text',
        options: props.config.reader?.options || {},
      },
      chunker: {
        strategy: chunkerStrategy,
        options: normalizedOptions,
      },
    }

    if (isVirtualFallbackContentProfile(props.config)) {
      applyReadonlyFallbackConstraints(form.value)
    } else if (isLockedFluidTopicsNativeProfile(props.config)) {
      applyLockedNativeProfileConstraints(form.value)
    }
  } else {
    isEditing.value = false
    form.value = getDefaultForm()
  }
  initialFormState.value = JSON.parse(JSON.stringify(form.value))
  isHydratingForm.value = false
}

const cancel = () => {
  emit('cancel')
  dialogOpen.value = false
}

const openPromptTemplateInNewTab = () => {
  const systemName = form.value.chunker.options.prompt_template_system_name
  if (!systemName) return
  const url = router.resolve({ name: 'PromptTemplatesItem', params: { id: systemName } }).href
  window.open(url, '_blank')
}

const save = async () => {
  if (isReadonlyProfile.value) {
    return
  }

  let isValid = true
  form.value.name = String(form.value.name || '').trim()

  // Validate required fields before submitting
  const isNameValid = isLockedNativeProfile.value || (nameRef.value as any)?.validate?.() !== false
  if (!isNameValid) {
    isValid &&= false
  }

  // Validate prompts when LLM strategy is selected
  if (isLLMStrategy.value) {
    const isPromptValid = (promptTemplateRef.value as any)?.validate?.() !== false
    if (!isPromptValid) {
      isValid &&= false
    }
  }

  if (!isValid) {
    return
  }

  const formData = JSON.parse(JSON.stringify(form.value))
  formData.name = String(formData.name || '').trim()

  if (Array.isArray(formData.source_ids)) {
    formData.source_ids = [...new Set(formData.source_ids.filter(Boolean))]
  }

  if (isLockedNativeProfile.value) {
    applyLockedNativeProfileConstraints(formData)
  }

  // Emit the configuration upwards for parent-managed saving
  emit('save', formData)
  dialogOpen.value = false
}

watch(
  () => form.value.reader.name,
  (readerName, previousReaderName) => {
    if (
      isHydratingForm.value ||
      isLockedNativeProfile.value ||
      isReadonlyProfile.value ||
      readerName !== SHAREPOINT_PAGE_READER ||
      readerName === previousReaderName
    ) {
      return
    }

    applySharePointPageDefaults(form.value)
  }
)

watch(
  () => props.showDialog,
  (newVal) => {
    dialogOpen.value = newVal
    if (newVal) {
      initForm()
      if (!isReadonlyProfile.value) {
        loadTemplates()
      }
    }
  }
)

watch(
  () => props.config,
  () => {
    if (dialogOpen.value) {
      initForm()
    }
  },
  { deep: true }
)
</script>

<style scoped>
.dialog-body {
  flex: 1 1 auto;
  overflow: auto;
}

:deep(.q-field__messages div[role='alert']) {
  font-size: var(--km-tiny-size, 10px);
  font-weight: 500;
  color: var(--q-error-text) !important;
}

.content-matching-sentence {
  font-size: var(--km-body-sm-size, 13px);
  line-height: 2;
  color: var(--q-secondary-text);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px;
  padding: 12px 16px;
  background: var(--q-primary-bg);
  border: 1px solid var(--q-border);
  border-radius: var(--radius-sm);
}
</style>
