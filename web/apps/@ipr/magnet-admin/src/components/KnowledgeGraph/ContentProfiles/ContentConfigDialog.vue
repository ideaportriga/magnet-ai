<template>
  <q-dialog v-model="dialogOpen" :persistent="!isReadonlyProfile && isDirty">
    <q-card class="q-px-lg q-py-sm" style="min-width: 900px; max-width: 900px; height: 820px; display: flex; flex-direction: column">
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
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Profile Name</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-md">Set profile name for this content configuration.</div>
            <km-input ref="nameRef" v-model="form.name" :rules="nameRules" :readonly="isLockedNativeProfile || isReadonlyProfile" required />
          </div>

          <!-- Content Source -->
          <div class="q-mb-lg">
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Matching & Reading</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-sm">Configure which content this profile applies to and how it is read.</div>
            <div class="content-matching-sentence q-mt-md">
              <template v-if="isReadonlyProfile">
                <span>This built-in profile is automatically used only when no other content profile matches.</span>
                <span>Content is read using</span>
                <kg-inline-field>
                  <span>{{ selectedReaderLabel }}</span>
                </kg-inline-field>
              </template>
              <template v-else-if="isLockedNativeProfile">
                <span>This profile automatically applies to all Fluid Topics sources using</span>
                <kg-inline-field>
                  <span>{{ selectedReaderLabel }}</span>
                </kg-inline-field>
              </template>
              <template v-else>
                <span>Read</span>
                <source-tree-dropdown v-model="sourceIdsModel" :sources="sources || []" />
                <span>matching</span>
                <kg-inline-field tooltip="Glob pattern (e.g. *.pdf). Separate multiple patterns with commas. Leave empty to match all.">
                  <input
                    v-model="form.glob_pattern"
                    class="kg-inline-field__input"
                    placeholder="any file"
                    spellcheck="false"
                    :style="{ width: patternInputWidth }"
                  >
                </kg-inline-field>
                <span>pattern using</span>
                <kg-inline-field interactive>
                  <span>{{ selectedReaderLabel }}</span>
                  <q-icon name="arrow_drop_down" size="16px" />
                  <q-menu anchor="bottom left" self="top left" :offset="[0, 4]">
                    <q-list dense style="min-width: 200px">
                      <q-item
                        v-for="option in selectableReaderOptions"
                        :key="option.value"
                        v-close-popup
                        clickable
                        :active="form.reader.name === option.value"
                        @click="form.reader.name = option.value"
                      >
                        <q-item-section>{{ option.label }}</q-item-section>
                      </q-item>
                    </q-list>
                  </q-menu>
                </kg-inline-field>
                <template v-if="isSourceMetadataReader">
                  <span>from field</span>
                  <kg-inline-field tooltip="Name of the metadata field to use as content (e.g., transcription)">
                    <input
                      ref="metadataFieldNameRef"
                      v-model="form.reader.options.field_name"
                      class="kg-inline-field__input"
                      placeholder="field name"
                      spellcheck="false"
                      :style="{ width: metadataFieldInputWidth }"
                    >
                  </kg-inline-field>
                </template>
              </template>
              <span class="chunking-strategy-description">
                {{ selectedReaderDescription }}
              </span>
            </div>
          </div>

          <!-- Processing & Chunking -->
          <div class="q-mb-lg">
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Processing & Chunking</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-sm">Configure how content is split into chunks.</div>
            <div class="content-matching-sentence q-mt-md">
              <template v-if="isReadonlyProfile">
                <span>This built-in fallback keeps the content as a single chunk up to the maximum size.</span>
              </template>
              <template v-else-if="isLockedNativeProfile">
                <span>Structured Fluid Topics content is already chunked upstream, so this reader always uses the built-in pre-chunked flow.</span>
              </template>
              <template v-else>
                <span>Split using</span>
                <kg-inline-field interactive>
                  <span>{{ selectedStrategyLabel }}</span>
                  <q-icon name="arrow_drop_down" size="16px" />
                  <q-menu anchor="bottom left" self="top left" :offset="[0, 4]">
                    <q-list dense style="min-width: 280px">
                      <q-item
                        v-for="option in chunkingStrategyOptions"
                        :key="option.value"
                        v-close-popup
                        clickable
                        :active="form.chunker.strategy === option.value"
                        @click="form.chunker.strategy = option.value"
                      >
                        <q-item-section>{{ option.label }}</q-item-section>
                      </q-item>
                    </q-list>
                  </q-menu>
                </kg-inline-field>
                <span>strategy, where the chunk content is treated as</span>
                <kg-inline-field v-if="isContentTypeLocked" :tooltip="contentTypeLockTooltip">
                  <span>{{ selectedContentTypeLabel }}</span>
                </kg-inline-field>
                <kg-inline-field v-else interactive>
                  <span>{{ selectedContentTypeLabel }}</span>
                  <q-icon name="arrow_drop_down" size="16px" />
                  <q-menu anchor="bottom left" self="top left" :offset="[0, 4]">
                    <q-list dense style="min-width: 220px">
                      <q-item
                        v-for="option in chunkContentTypeOptions"
                        :key="option.value"
                        v-close-popup
                        clickable
                        :active="form.chunker.options.chunk_content_type === option.value"
                        @click="form.chunker.options.chunk_content_type = option.value"
                      >
                        <q-item-section>{{ option.label }}</q-item-section>
                      </q-item>
                    </q-list>
                  </q-menu>
                </kg-inline-field>
                <span>.</span>
              </template>
              <span v-if="!isReadonlyProfile && !isLockedNativeProfile" class="chunking-strategy-description">
                {{ selectedChunkingStrategyDescription }}
              </span>
            </div>

            <!-- Chunk Max Size & Overlap -->
            <div v-if="!isReadonlyProfile && !isLockedNativeProfile" class="q-mt-md">
              <div class="row q-col-gutter-lg">
                <div class="col-6">
                  <div class="km-input-label q-pb-xs">Chunk Max Size (characters)</div>
                  <km-input v-model.number="form.chunker.options.chunk_max_size" type="number" :min="100" placeholder="18000" />
                </div>
                <div v-if="isRecursiveStrategy || isKreuzbergStrategy" class="col-6">
                  <div class="km-input-label q-pb-xs">Chunk Overlap (%)</div>
                  <div class="row items-center" style="height: 36px">
                    <q-slider
                      v-model="form.chunker.options.recursive_chunk_overlap"
                      :min="0"
                      :max="0.9"
                      :step="0.02"
                      label
                      :label-value="`${Math.round((form.chunker.options.recursive_chunk_overlap || 0) * 100)}%`"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Prompt Template (LLM / HTML LLM) -->
            <div v-if="!isLockedNativeProfile && !isReadonlyProfile && (isLLMStrategy || isHtmlLlmStrategy)" class="q-mt-md">
              <div class="km-input-label q-pb-xs">Prompt Template</div>
              <div class="row q-gap-8 no-wrap">
                <km-select
                  v-model="form.chunker.options.prompt_template_system_name"
                  placeholder="Select a prompt template"
                  class="col-grow"
                  :options="templateOptions"
                  :loading="loadingTemplates"
                  emit-value
                  map-options
                  option-value="system_name"
                  option-label="name"
                />
                <q-btn
                  v-if="form.chunker.options.prompt_template_system_name"
                  flat
                  dense
                  icon="fa fa-external-link"
                  color="secondary-text"
                  size="sm"
                  @click="openPromptTemplateInNewTab"
                />
              </div>
            </div>

            <!-- Advanced settings -->
            <div class="advanced-settings q-mt-md" :class="{ 'advanced-settings--expanded': isAdvancedExpanded }">
              <q-expansion-item
                v-model="isAdvancedExpanded"
                class="advanced-settings__expansion"
                header-class="advanced-settings__header"
                expand-icon-class="advanced-settings__caret"
                dense
              >
                <template #header>
                  <q-item-section>
                    <div class="advanced-settings__title">Advanced settings</div>
                    <div class="advanced-settings__subtitle">Customize titles and chunking behavior</div>
                  </q-item-section>
                </template>
                <div class="advanced-settings__content">
                  <!-- Chunk Title & Document Title -->
                  <div class="row q-col-gutter-lg">
                    <div class="col-6">
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

                    <div class="col-6">
                      <div class="km-input-label q-pb-xs">Document Title</div>
                      <km-input
                        v-model="form.chunker.options.document_title_pattern"
                        :readonly="isReadonlyProfile"
                        placeholder="e.g., {title} — {filename}"
                      >
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

                  <!-- Recursive: Splitters -->
                  <div v-if="!isLockedNativeProfile && isRecursiveStrategy" class="q-mt-md">
                    <div class="km-input-label q-pb-xs">Chunk Splitters</div>
                    <div class="splitters-container q-py-xs">
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
                            style="height: 24px; width: 28px; border-radius: 4px"
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

                  <!-- LLM / HTML LLM: Handling Content Size -->
                  <div v-if="!isLockedNativeProfile && (isLLMStrategy || isHtmlLlmStrategy)" class="q-mt-md">
                    <div class="km-input-label q-pb-xs">Handling Content Size</div>
                    <div class="km-description text-secondary-text q-mb-md">
                      LLMs have limited context window, so content must be divided into smaller segments before executing LLM-based chunking. The
                      <b>Segment Overlap</b>
                      parameter controls content repetition between consecutive segments. The
                      <b>Last Segment Allowed Expansion</b>
                      parameter allows the final segment to be expanded beyond the normal segment size to reduce small trailing remainders.
                    </div>
                    <div class="row q-col-gutter-lg">
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
                </div>
              </q-expansion-item>
            </div>
          </div>

          <!-- Chunk Indexing -->
          <div class="q-mb-lg">
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Indexing</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-sm">Configure how chunk content is indexed for vector search.</div>
            <div class="content-matching-sentence q-mt-md">
              <template v-if="isReadonlyProfile">
                <span>Chunks are indexed as a whole — the entire chunk content is embedded as a single vector.</span>
              </template>
              <template v-else-if="isLockedNativeProfile">
                <span>Chunks are indexed as a whole — the entire chunk content is embedded as a single vector.</span>
              </template>
              <template v-else>
                <span>Index each chunk by</span>
                <kg-inline-field interactive>
                  <span>{{ selectedIndexingModeLabel }}</span>
                  <q-icon name="arrow_drop_down" size="16px" />
                  <q-menu anchor="bottom left" self="top left" :offset="[0, 4]">
                    <q-list dense style="min-width: 280px">
                      <q-item
                        v-for="option in indexingModeOptions"
                        :key="option.value"
                        v-close-popup
                        clickable
                        :active="form.chunker.options.indexing_mode === option.value"
                        @click="form.chunker.options.indexing_mode = option.value"
                      >
                        <q-item-section>{{ option.menuLabel }}</q-item-section>
                      </q-item>
                    </q-list>
                  </q-menu>
                </kg-inline-field>
                <template v-if="form.chunker.options.indexing_mode === 'whole'">
                  <span>, but if it exceeds the maximum size -</span>
                  <kg-inline-field interactive>
                    <span>{{ selectedOverflowStrategyLabel }}</span>
                    <q-icon name="arrow_drop_down" size="16px" />
                    <q-menu anchor="bottom left" self="top left" :offset="[0, 4]">
                      <q-list dense style="min-width: 220px">
                        <q-item
                          v-for="option in indexingOverflowOptions"
                          :key="option.value"
                          v-close-popup
                          clickable
                          :active="form.chunker.options.indexing_overflow_strategy === option.value"
                          @click="form.chunker.options.indexing_overflow_strategy = option.value"
                        >
                          <q-item-section>{{ option.menuLabel }}</q-item-section>
                        </q-item>
                      </q-list>
                    </q-menu>
                  </kg-inline-field>
                </template>
                <template v-if="showIndexingPartSize">
                  <span>with a fixed size of</span>
                  <kg-inline-field tooltip="Size of each part in characters. Must be less than chunk max size.">
                    <input
                      :value="form.chunker.options.indexing_part_size"
                      class="kg-inline-field__input kg-inline-field__input--no-spinners"
                      type="number"
                      min="1"
                      :max="(form.chunker.options.chunk_max_size || 1) - 1"
                      placeholder="500"
                      :style="{ width: indexingPartSizeInputWidth }"
                      @input="onIndexingPartSizeInput"
                    >
                  </kg-inline-field>
                  <span>characters and an overlap of</span>
                  <kg-inline-field tooltip="Percentage of overlap between consecutive parts (0–90%)">
                    <input
                      :value="Math.round((form.chunker.options.indexing_part_overlap || 0) * 100)"
                      class="kg-inline-field__input kg-inline-field__input--no-spinners"
                      type="number"
                      min="0"
                      max="90"
                      placeholder="0"
                      :style="{ width: indexingPartOverlapInputWidth }"
                      @input="onIndexingPartOverlapInput"
                    >
                  </kg-inline-field>
                  <span>%.</span>
                </template>
              </template>
              <span v-if="!isReadonlyProfile && !isLockedNativeProfile" class="chunking-strategy-description">
                {{ combinedIndexingDescription }}
              </span>
            </div>
          </div>
        </q-form>
      </q-card-section>

      <q-card-actions class="q-py-lg q-pr-lg">
        <km-btn :label="dismissLabel" flat color="primary" @click="cancel" />
        <q-space v-if="!isReadonlyProfile" />
        <km-btn v-if="!isReadonlyProfile" label="Save" @click="save" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import router from '@/router'
import { fetchData, required } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import KgInlineField from '../common/KgInlineField.vue'
import type { SourceRow } from '../Sources/models'
import type { ContentConfigRow } from './models'
import {
  chunkContentTypeOptions,
  chunkingStrategyOptions,
  indexingModeOptions,
  indexingOverflowOptions,
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
  SOURCE_METADATA_READER,
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
const store = useStore()
const $q = useQuasar()

const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
    console.error('Error loading prompt templates:', error)
    $q.notify({ type: 'negative', message: 'Failed to load prompt templates' })
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
      recursive_chunk_overlap: 0.1,
      chunk_max_size: 15000,
      splitters: ['\n\n', '\n', ' ', ''],
      prompt_template_system_name: '',
      document_title_pattern: '',
      chunk_title_pattern: '',
      chunk_content_type: 'plain_text',
      indexing_mode: 'whole',
      indexing_overflow_strategy: 'truncate',
      indexing_part_size: 500,
      indexing_part_overlap: 0,
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

const metadataFieldInputWidth = computed(() => {
  const value = form.value.reader.options?.field_name || ''
  if (!value) {
    return '10ch'
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
      // Recursive strategy
      recursive_chunk_overlap: 0.1,
      // Chunk-level constraints (applies to all strategies)
      chunk_max_size: 18000,
      splitters: ['\n\n', '\n', ' ', ''],
      prompt_template_system_name: '',
      // Optional pattern for document title generation
      document_title_pattern: '',
      // Optional pattern for chunk title generation
      chunk_title_pattern: '',
      // Chunk content type
      chunk_content_type: 'plain_text',
      // Chunk indexing settings
      indexing_mode: 'whole',
      indexing_overflow_strategy: 'truncate',
      indexing_part_size: 500,
      indexing_part_overlap: 0,
    },
  },
})

const form = ref(getDefaultForm())
const initialFormState = ref(getDefaultForm())
const nameRef = ref()
const metadataFieldNameRef = ref()
const newSplitter = ref('')
const showNewSplitterInput = ref(false)
const newSplitterInput = ref()
const isHydratingForm = ref(false)
const isAdvancedExpanded = ref(false)
const isReadonlyProfile = computed(() => isEditing.value && isVirtualFallbackContentProfile(props.config ?? form.value))
const dialogTitle = computed(() => (isReadonlyProfile.value ? 'View Content Profile' : `${isEditing.value ? 'Edit' : 'Add'} Content Profile`))
const dismissLabel = computed(() => (isReadonlyProfile.value ? 'Close' : 'Cancel'))
const isLockedNativeProfile = computed(() => isEditing.value && isLockedFluidTopicsNativeProfile(props.config ?? form.value))
const isSharePointPageReader = computed(() => form.value.reader.name === SHAREPOINT_PAGE_READER)
const isSourceMetadataReader = computed(() => form.value.reader.name === SOURCE_METADATA_READER)
const selectedReaderLabel = computed(() => {
  const option = readerOptions.find((o) => o.value === form.value.reader.name)
  return option?.label ?? form.value.reader.name
})
const selectedReaderDescription = computed(() => {
  const option = readerOptions.find((o) => o.value === form.value.reader.name)
  return option?.description || ''
})
const selectedStrategyLabel = computed(() => {
  const option = chunkingStrategyOptions.find((o) => o.value === form.value.chunker.strategy)
  return option?.label ?? form.value.chunker.strategy
})
const isLLMStrategy = computed(() => form.value.chunker.strategy === 'llm')
const isHtmlLlmStrategy = computed(() => form.value.chunker.strategy === 'html_llm')
const isRecursiveStrategy = computed(() => form.value.chunker.strategy === 'recursive_character_text_splitting')
const isKreuzbergStrategy = computed(() => form.value.chunker.strategy === 'kreuzberg')
const lockedContentType = computed<'markdown' | 'html' | null>(() => {
  if (isHtmlLlmStrategy.value) return 'html'
  if (isLLMStrategy.value || isKreuzbergStrategy.value) return 'markdown'
  return null
})
const isContentTypeLocked = computed(() => lockedContentType.value !== null)
const selectedContentTypeLabel = computed(() => {
  const value = form.value.chunker.options.chunk_content_type
  return chunkContentTypeOptions.find((o) => o.value === value)?.label ?? value
})
const contentTypeLockTooltip = computed(() => {
  if (isHtmlLlmStrategy.value) return 'This strategy always produces HTML chunks.'
  if (isLLMStrategy.value || isKreuzbergStrategy.value) return 'This strategy always produces Markdown chunks.'
  return ''
})
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
const selectedIndexingModeLabel = computed(() => {
  const option = indexingModeOptions.find((o) => o.value === form.value.chunker.options.indexing_mode)
  return option?.label ?? form.value.chunker.options.indexing_mode
})
const selectedOverflowStrategyLabel = computed(() => {
  const option = indexingOverflowOptions.find((o) => o.value === form.value.chunker.options.indexing_overflow_strategy)
  return option?.label ?? form.value.chunker.options.indexing_overflow_strategy
})
const combinedIndexingDescription = computed(() => {
  const modeOption = indexingModeOptions.find((o) => o.value === form.value.chunker.options.indexing_mode)
  const modeDesc = modeOption?.description || ''
  if (form.value.chunker.options.indexing_mode !== 'whole') {
    return modeDesc
  }
  const overflowOption = indexingOverflowOptions.find((o) => o.value === form.value.chunker.options.indexing_overflow_strategy)
  const overflowDesc = overflowOption?.description || ''
  return [modeDesc, overflowDesc].filter(Boolean).join(' ')
})
const showIndexingPartSize = computed(() => {
  return (
    form.value.chunker.options.indexing_mode === 'fixed_parts' ||
    (form.value.chunker.options.indexing_mode === 'whole' && form.value.chunker.options.indexing_overflow_strategy === 'split')
  )
})
const indexingPartSizeInputWidth = computed(() => {
  const value = String(form.value.chunker.options.indexing_part_size || '')
  if (!value) {
    return '4ch'
  }
  return `${value.length + 1}ch`
})
const indexingPartOverlapInputWidth = computed(() => {
  const value = String(Math.round((form.value.chunker.options.indexing_part_overlap || 0) * 100))
  if (!value || value === '0') {
    return '2ch'
  }
  return `${value.length + 1}ch`
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

const enforceContentTypeLock = () => {
  if (lockedContentType.value !== null) {
    form.value.chunker.options.chunk_content_type = lockedContentType.value
  }
}

const onIndexingPartSizeInput = (event: Event) => {
  const inputEl = event.target as HTMLInputElement
  const rawValue = inputEl.value.trim()
  if (rawValue === '') {
    form.value.chunker.options.indexing_part_size = ''
    return
  }
  const raw = Number(rawValue)
  const maxAllowed = (Number(form.value.chunker.options.chunk_max_size) || 1) - 1
  const clamped = Math.max(1, Math.min(raw || 1, maxAllowed))
  form.value.chunker.options.indexing_part_size = clamped
  inputEl.value = String(clamped)
}

const onIndexingPartOverlapInput = (event: Event) => {
  const inputEl = event.target as HTMLInputElement
  const rawValue = inputEl.value.trim()
  if (rawValue === '') {
    form.value.chunker.options.indexing_part_overlap = 0
    return
  }
  const raw = Number(rawValue)
  const clamped = Math.max(0, Math.min(raw || 0, 90))
  form.value.chunker.options.indexing_part_overlap = clamped / 100
  inputEl.value = String(clamped)
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
      chunk_max_size: typeof chunkerOptions.chunk_max_size !== 'undefined' ? chunkerOptions.chunk_max_size : (chunkerOptions.llm_batch_size ?? 18000),
      // prefer new recursive_*; fall back to legacy rc_* and old batch_* keys
      recursive_chunk_overlap: chunkerOptions.recursive_chunk_overlap ?? chunkerOptions.rc_chunk_overlap ?? chunkerOptions.batch_overlap ?? 0.1,
      splitters: chunkerOptions.splitters || ['\n\n', '\n', ' ', ''],
      prompt_template_system_name: chunkerOptions.prompt_template_system_name,
      document_title_pattern: chunkerOptions.document_title_pattern || '',
      chunk_title_pattern: chunkerOptions.chunk_title_pattern || '',
      chunk_content_type: chunkerOptions.chunk_content_type || 'plain_text',
      indexing_mode: chunkerOptions.indexing_mode || 'whole',
      indexing_overflow_strategy: chunkerOptions.indexing_overflow_strategy || 'truncate',
      indexing_part_size: chunkerOptions.indexing_part_size ?? 500,
      indexing_part_overlap: chunkerOptions.indexing_part_overlap ?? 0,
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
  enforceContentTypeLock()
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

  // Validate metadata field name when source metadata reader is selected
  if (isSourceMetadataReader.value && !form.value.reader.options?.field_name?.trim()) {
    isValid = false
    $q.notify({ type: 'negative', message: 'Metadata field name is required.' })
  }

  // Validate prompts when LLM strategy is selected
  if ((isLLMStrategy.value || isHtmlLlmStrategy.value) && !form.value.chunker.options.prompt_template_system_name) {
    isValid = false
    $q.notify({ type: 'negative', message: 'Prompt template is required for LLM-based chunking.' })
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
  () => form.value.chunker.strategy,
  () => {
    if (isHydratingForm.value) return
    enforceContentTypeLock()
  }
)

watch(
  () => props.showDialog,
  (newVal) => {
    dialogOpen.value = newVal
    if (newVal) {
      isAdvancedExpanded.value = false
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
  font-size: 10px;
  font-weight: 500;
  color: var(--q-error-text) !important;
}

.chunking-strategy-description {
  width: 100%;
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px dashed rgba(var(--q-primary-rgb, 25, 118, 210), 0.2);
  font-size: 12px;
  line-height: 1.5;
  opacity: 0.8;
}

.content-matching-sentence {
  font-size: 13px;
  line-height: 2;
  color: var(--q-secondary-text);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(var(--q-primary-rgb, 25, 118, 210), 0.06);
  border: 1px solid rgba(var(--q-primary-rgb, 25, 118, 210), 0.2);
  border-radius: 4px;
}

.kg-inline-field__input--no-spinners::-webkit-outer-spin-button,
.kg-inline-field__input--no-spinners::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.kg-inline-field__input--no-spinners {
  -moz-appearance: textfield;
}

.advanced-settings {
  border: 1px solid rgba(var(--q-primary-rgb, 25, 118, 210), 0.2);
  border-radius: 6px;
  background: rgba(var(--q-primary-rgb, 25, 118, 210), 0.04);
  overflow: hidden;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.advanced-settings:hover {
  border-color: rgba(var(--q-primary-rgb, 25, 118, 210), 0.35);
}

.advanced-settings--expanded {
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.advanced-settings__expansion :deep(.q-expansion-item__container) {
  border: none;
}

.advanced-settings__expansion :deep(.q-item) {
  padding: 0;
  min-height: 48px;
  background: transparent;
}

.advanced-settings__expansion :deep(.advanced-settings__header) {
  padding: 8px 14px;
  min-height: 48px;
  transition: background 0.2s ease;
}

.advanced-settings__expansion :deep(.advanced-settings__header:hover) {
  background: rgba(var(--q-primary-rgb, 25, 118, 210), 0.06);
}

.advanced-settings__expansion :deep(.q-focus-helper) {
  display: none;
}

.advanced-settings__title {
  font-size: 13px;
  font-weight: 600;
  color: #24292f;
  letter-spacing: 0.01em;
}

.advanced-settings__subtitle {
  font-size: 11px;
  color: var(--q-secondary-text);
  margin-top: 2px;
  line-height: 1.4;
}

.advanced-settings__expansion :deep(.advanced-settings__caret) {
  color: var(--q-primary);
}

.advanced-settings__expansion :deep(.q-expansion-item__content) {
  padding: 0;
}

.advanced-settings__content {
  padding: 16px;
  border-top: 1px solid rgba(var(--q-primary-rgb, 25, 118, 210), 0.15);
  background: white;
}

.advanced-settings .splitters-container {
  border: 1px solid var(--q-control-border, #d0d7de);
  border-radius: 4px;
  padding: 4px 8px;
  background: #fafbfc;
}
</style>
