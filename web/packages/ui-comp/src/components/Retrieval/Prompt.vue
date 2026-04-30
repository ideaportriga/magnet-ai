<script setup lang="ts">
/**
 * Retrieval prompt input — used by both `magnet-admin` and `magnet-panel`
 * to fire a retrieval request. Rewritten on `@ds` in Phase 4c. Public
 * surface preserved: `hideCollectionPicker`, `retrieval`, `retrieval_tool`,
 * `searchString`, `t`. Emits `onLoad`, `searchRetrieval`,
 * `searchRetrievalExecute`. `refine(question)` exposed via defineExpose.
 */

import { computed, ref, useTemplateRef, watch } from 'vue'
import useState from '@shared/composables/useState'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmInput from '@ds/components/domain/KmInput.vue'

const DEFAULT_T = { placeholder: 'Type your question here' }

const props = withDefaults(
  defineProps<{
    hideCollectionPicker?: boolean
    retrieval?: boolean
    /** Underscore name kept for backwards compatibility with existing callers. */
    retrieval_tool?: string
    searchString?: string
    t?: Record<string, string>
  }>(),
  {
    hideCollectionPicker: false,
    retrieval: false,
    retrieval_tool: '',
    searchString: '',
    t: () => ({}),
  },
)

const emit = defineEmits<{
  onLoad: []
  searchRetrieval: []
  searchRetrievalExecute: [retrieval_tool: string]
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
  if (props.retrieval) emit('searchRetrieval')
  else emit('searchRetrievalExecute', props.retrieval_tool)

  prompt.value = ''
  inputRef.value?.blur()
  emit('onLoad')
}

defineExpose({ refine })
</script>

<template>
  <div class="retrieval-prompt stack" data-gap="sm">
    <KmInput
      ref="input"
      autogrow
      :min-rows="1"
      :max-rows="10"
      :placeholder="mergedT.placeholder"
      :model-value="prompt"
      class="retrieval-prompt__input"
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
          aria-label="Search"
          @click="getAnswer"
        />
      </template>
    </KmInput>
  </div>
</template>

<style scoped>
.retrieval-prompt {
  border-radius: var(--ds-radius-xl);
  margin-block-end: var(--ds-space-lg);
  inline-size: 100%;
  min-inline-size: 450px;
  max-inline-size: 800px;
}

@media (max-width: 500px) {
  .retrieval-prompt { min-inline-size: unset; max-inline-size: unset; }
}

</style>
