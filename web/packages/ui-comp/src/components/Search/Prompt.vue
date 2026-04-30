<script setup lang="ts">
/**
 * Search prompt input — RAG variant. Same shape as `Retrieval/Prompt.vue`
 * but emits the RAG event family. Rewritten on `@ds`.
 */

import { computed, useTemplateRef, watch } from 'vue'
import useState from '@shared/composables/useState'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmInput from '@ds/components/domain/KmInput.vue'

const DEFAULT_T = { placeholder: 'Type your question here' }

const props = withDefaults(
  defineProps<{
    hideCollectionPicker?: boolean
    rag?: boolean
    /** Underscore name kept for backwards compatibility with existing callers. */
    rag_code?: string
    searchString?: string
    t?: Record<string, string>
  }>(),
  {
    hideCollectionPicker: false,
    rag: false,
    rag_code: '',
    searchString: '',
    t: () => ({}),
  },
)

const emit = defineEmits<{
  onLoad: []
  search: []
  searchRag: []
  searchRagExecute: [rag_code: string]
}>()

const prompt = useState('searchPrompt')
const inputRef = useTemplateRef<{ focus: () => void; blur: () => void }>('input')

const mergedT = computed(() => ({ ...DEFAULT_T, ...props.t }))

watch(
  () => props.searchString,
  (next, prev) => {
    if (prev !== next) prompt.value = next || ''
  },
)

function refine(question: string) {
  prompt.value = question
  inputRef.value?.focus()
}

function updatePrompt(value: string) {
  prompt.value = value
}

function submit(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return
  event.preventDefault()
  void getAnswer()
}

async function getAnswer() {
  if (props.rag) emit('searchRag')
  else emit('searchRagExecute', props.rag_code)

  prompt.value = ''
  inputRef.value?.blur()
  emit('onLoad')
}

defineExpose({ refine })
</script>

<template>
  <div class="search-prompt stack" data-gap="sm">
    <KmInput
      ref="input"
      autogrow
      :min-rows="1"
      :max-rows="10"
      data-test="search-input"
      :placeholder="mergedT.placeholder"
      :model-value="prompt"
      class="search-prompt__input"
      @input="updatePrompt"
      @keydown="submit"
    >
      <template #append>
        <KmBtn
          type="button"
          size="icon-xs"
          icon="search"
          icon-size="16px"
          icon-tone="inverse"
          data-test="search-btn"
          aria-label="Search"
          @click="getAnswer"
        />
      </template>
    </KmInput>
  </div>
</template>

<style scoped>
.search-prompt {
  border-radius: var(--ds-radius-xl);
  margin-block-end: var(--ds-space-lg);
  inline-size: 100%;
  min-inline-size: 450px;
  max-inline-size: 800px;
}
@media (max-width: 500px) {
  .search-prompt { min-inline-size: unset; max-inline-size: unset; }
}

</style>
