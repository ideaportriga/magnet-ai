<template>
  <q-dialog v-model="dialogOpen" :persistent="isDirty">
    <q-card class="q-px-lg q-py-sm" style="min-width: 800px; max-width: 800px; height: 820px; display: flex; flex-direction: column">
      <q-card-section>
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">{{ isEditing ? 'Edit' : 'Add' }} Content Configuration</div>
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
                <km-input ref="nameRef" v-model="form.name" :rules="[required()]" :disable="isEditing" required />
              </div>

              <!-- Content Reader -->
              <div class="col-6">
                <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Content Reader</div>
                <div class="km-description text-secondary-text q-mt-xs q-mb-md">Select tool used to read the content.</div>
                <km-select v-model="form.reader.name" :options="readerOptions" emit-value map-options />
              </div>
            </div>
          </div>

          <div class="q-mb-lg">
            <!-- Content Matching -->
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Content Matching</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-md">
              Select source types and file pattern to which this configuration applies. Use glob pattern syntax to match content, separate multiple
              patterns with commas. If source doesn't support file pattern, leave it blank - empty pattern matches all content.
            </div>
            <div class="row q-col-gutter-lg">
              <!-- Source types -->
              <div class="col-6">
                <div class="km-input-label q-pb-sm">Source Types</div>
                <q-field borderless dense :error="!!sourceTypesError" :error-message="sourceTypesError" no-error-icon hide-bottom-space>
                  <template #control>
                    <div class="row q-gutter-xs">
                      <q-btn
                        v-for="sourceType in sourceTypeOptions"
                        :key="sourceType.value"
                        :color="isSourceTypeSelected(sourceType.value) ? 'grey-2' : 'grey-5'"
                        :unelevated="isSourceTypeSelected(sourceType.value)"
                        :flat="!isSourceTypeSelected(sourceType.value)"
                        :outline="!isSourceTypeSelected(sourceType.value)"
                        :ripple="false"
                        dense
                        :class="['source-type-toggle', { 'is-selected': isSourceTypeSelected(sourceType.value) }]"
                        @click="toggleSourceType(sourceType.value)"
                      >
                        <template v-if="sourceType.image">
                          <q-img :src="sourceType.image" width="20px" height="20px" no-spinner no-transition />
                        </template>
                        <template v-else-if="sourceType.icon">
                          <q-icon :name="sourceType.icon" size="18px" color="black" />
                        </template>
                        <q-tooltip>{{ sourceType.label }}</q-tooltip>
                      </q-btn>
                    </div>
                  </template>
                  <template #error>
                    <div class="km-small-chip q-pa-4 q-pl-8 text-error-text">dasfsdf</div>
                  </template>
                </q-field>
              </div>
              <!-- File pattern -->
              <div class="col-6">
                <div class="km-input-label q-pb-sm">File Pattern</div>
                <km-input v-model="form.glob_pattern" placeholder="e.g., *.pdf" />
              </div>
            </div>
          </div>

          <div class="q-mb-lg">
            <!-- Chunking Strategy -->
            <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Chunking Strategy</div>
            <div class="km-description text-secondary-text q-mt-xs q-mb-md">Select the strategy used to split content into chunks.</div>
            <div class="row q-col-gutter-lg items-center">
              <div class="col-4">
                <km-select v-model="form.chunker.strategy" :options="chunkingStrategyOptions" emit-value map-options />
              </div>
              <div class="col-8">
                <div class="km-description">{{ selectedChunkingStrategyDescription }}</div>
              </div>
            </div>
            <div
              v-if="isLLMStrategy"
              class="km-description q-mt-lg row items-center q-gap-8 q-pa-md rounded-borders bg-yellow-1 text-yellow-10"
              style="border: 1px solid var(--q-warning)"
            >
              <q-icon name="warning" color="yellow-8" size="26px" />
              <div class="col">LLM-based chunking may incur significant costs and can run for a long time, especially on large documents.</div>
            </div>
          </div>

          <template v-if="isLLMStrategy">
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

          <template v-if="isLLMStrategy">
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

          <template v-if="isRecursiveStrategy">
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
                  <div class="splitters-container q-py-xs" style="border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 4px">
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
              <km-input v-model="form.chunker.options.document_title_pattern" placeholder="e.g., {title} — {filename}">
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
                <km-input v-model="form.chunker.options.chunk_title_pattern" placeholder="e.g., Chunk {index} — Page {page}">
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
                <km-input v-model.number="form.chunker.options.chunk_max_size" type="number" min="100" required />
              </div>
            </div>
          </div>
        </q-form>
      </q-card-section>

      <q-card-actions class="q-py-lg q-pr-lg">
        <km-btn label="Cancel" flat color="primary" @click="cancel" />
        <km-btn v-if="isEditing" flat icon="fas fa-trash" icon-size="14px" icon-color="negative" class="q-ml-sm" @click="confirmDelete" />
        <q-space />
        <km-btn label="Save" @click="save" />
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
import { chunkingStrategyOptions, readerOptions, sourceTypeOptions } from './models'

const props = defineProps<{
  showDialog: boolean
  config?: any
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'save', value: any): void
  (e: 'cancel'): void
  (e: 'delete', value: string): void
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

const allSourceTypeValues = sourceTypeOptions.map((o) => o.value)

const selectedChunkingStrategyDescription = computed(() => {
  const option = chunkingStrategyOptions.find((o) => o.value === form.value.chunker.strategy)
  return option?.description || ''
})

const defaultForm = {
  name: '',
  enabled: true,
  glob_pattern: '',
  source_types: allSourceTypeValues,
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
}

const form = ref(JSON.parse(JSON.stringify(defaultForm)))
const initialFormState = ref(JSON.parse(JSON.stringify(defaultForm)))
const nameRef = ref()
const promptTemplateRef = ref()
const newSplitter = ref('')
const showNewSplitterInput = ref(false)
const newSplitterInput = ref()
const sourceTypesError = ref('')

// Computed properties for conditional rendering
const isLLMStrategy = computed(() => form.value.chunker.strategy === 'llm')
const isRecursiveStrategy = computed(() => form.value.chunker.strategy === 'recursive_character_text_splitting')
const isDirty = computed(() => JSON.stringify(form.value) !== JSON.stringify(initialFormState.value))

// Source type toggle functions
const isSourceTypeSelected = (sourceType: string): boolean => {
  if (!form.value.source_types || form.value.source_types.length === 0) {
    return false
  }
  return form.value.source_types.includes(sourceType)
}

const toggleSourceType = (sourceType: string) => {
  if (!form.value.source_types) {
    form.value.source_types = []
  }
  const index = form.value.source_types.indexOf(sourceType)
  if (index > -1) {
    form.value.source_types.splice(index, 1)
  } else {
    form.value.source_types.push(sourceType)
  }
}

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
  if (props.config) {
    isEditing.value = true

    // Parse chunker config
    const chunkerStrategy = props.config.chunker?.strategy || 'recursive_character_text_splitting'
    const chunkerOptions = props.config.chunker?.options || {}
    // Backward compatibility: map old keys batch_size/batch_overlap if present
    const hasLegacy = typeof chunkerOptions.batch_size !== 'undefined' || typeof chunkerOptions.batch_overlap !== 'undefined'
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

    form.value = {
      name: props.config.name || '',
      enabled: props.config.enabled ?? true,
      glob_pattern: props.config.glob_pattern || '',
      source_types:
        Array.isArray(props.config.source_types) && props.config.source_types.length > 0 ? props.config.source_types : allSourceTypeValues,
      reader: {
        name: props.config.reader?.name || 'default',
        options: props.config.reader?.options || {},
      },
      chunker: {
        strategy: chunkerStrategy,
        options: normalizedOptions,
      },
    }
  } else {
    isEditing.value = false
    form.value = JSON.parse(JSON.stringify(defaultForm))
  }
  initialFormState.value = JSON.parse(JSON.stringify(form.value))
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
  let isValid = true

  // Validate required fields before submitting
  const isNameValid = (nameRef.value as any)?.validate?.() !== false
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

  // Enforce at least one source type selected
  if (!form.value.source_types || form.value.source_types.length === 0) {
    sourceTypesError.value = 'Select at least one source type'
    isValid &&= false
  } else {
    sourceTypesError.value = ''
  }

  if (!isValid) {
    return
  }

  const formData = JSON.parse(JSON.stringify(form.value))

  // Emit the configuration upwards for parent-managed saving
  emit('save', formData)
  dialogOpen.value = false
}

const confirmDelete = () => {
  const name = form.value?.name
  if (!name) return
  $q.dialog({
    title: 'Delete content configuration',
    message: `Are you sure you want to delete "${name}"?`,
    cancel: true,
    persistent: true,
    ok: { label: 'Delete', color: 'negative' },
  }).onOk(() => {
    emit('delete', name)
    dialogOpen.value = false
  })
}

watch(
  () => props.showDialog,
  (newVal) => {
    dialogOpen.value = newVal
    if (newVal) {
      initForm()
      loadTemplates()
    }
  }
)

// Clear source type error once at least one is selected after validation
watch(
  () => (form.value.source_types || []).length,
  (len) => {
    if (len > 0 && sourceTypesError.value) {
      sourceTypesError.value = ''
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

.source-type-toggle {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  transition: none;
}
.source-type-toggle.is-selected {
  background-color: #ede7f6 !important; /* faded purple */
  border: 1px solid #b39ddb !important; /* purple border */
}
:deep(.q-field__messages div[role='alert']) {
  font-size: 10px;
  font-weight: 500;
  color: var(--q-error-text) !important;
}
</style>
