<template>
  <kg-dialog-base
    :model-value="showDialog"
    :title="isNew ? m.retrieval_addExampleTitle() : m.retrieval_editExampleTitle()"
    :subtitle="m.retrieval_exampleSubtitle()"
    :confirm-label="isNew ? m.retrieval_addExample() : m.retrieval_saveChanges()"
    :disable-confirm="!isValid"
    size="md"
    @update:model-value="$emit('update:showDialog', $event)"
    @cancel="handleClose"
    @confirm="handleSave"
  >
    <!-- Example Label Section -->
    <kg-dialog-section
      :title="m.retrieval_exampleLabelSection()"
      :description="m.retrieval_exampleLabelDesc()"
      icon="label"
      icon-color="blue-7"
      focus-highlight
    >
      <km-input
        v-model="form.title"
        :placeholder="m.retrieval_exampleLabelPlaceholder()"
      />
    </kg-dialog-section>

    <!-- User Message Section -->
    <kg-dialog-section
      :title="m.retrieval_userMessageSection()"
      :description="m.retrieval_userMessageDesc()"
      icon="chat_bubble_outline"
      icon-color="teal-7"
      focus-highlight
    >
      <km-input
        v-model="form.input"
        type="textarea"
        autogrow
        rows="3"
        :placeholder="m.retrieval_userMessagePlaceholder()"
      />
    </kg-dialog-section>

    <!-- Agent Response Section -->
    <kg-dialog-section
      :title="m.retrieval_agentResponse()"
      :description="m.retrieval_agentResponseDesc()"
      icon="smart_toy"
      icon-color="deep-purple-6"
      focus-highlight
    >
      <km-input
        v-model="form.output"
        type="textarea"
        autogrow
        rows="4"
        :placeholder="m.retrieval_agentResponsePlaceholder()"
      />
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { m } from '@/paraglide/messages'
import { KgDialogBase, KgDialogSection } from '../common';
import type { RetrievalExample } from './models';

const props = defineProps<{
  showDialog: boolean
  example: RetrievalExample | null
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'save', example: RetrievalExample): void
}>()

const isNew = ref(true)

const form = ref<RetrievalExample>({
  id: '',
  title: '',
  input: '',
  output: '',
})

const isValid = computed(() => {
  return form.value.title.trim() && form.value.input.trim() && form.value.output.trim()
})

watch(
  () => props.showDialog,
  (open) => {
    if (open) {
      if (props.example) {
        isNew.value = false
        form.value = { ...props.example }
      } else {
        isNew.value = true
        form.value = {
          id: '',
          title: '',
          input: '',
          output: '',
        }
      }
    }
  },
  { immediate: true }
)

const handleClose = () => {
  emit('update:showDialog', false)
}

const handleSave = () => {
  emit('save', { ...form.value })
  emit('update:showDialog', false)
}
</script>
