<template>
  <kg-dialog-base
    :model-value="showDialog"
    :title="isNew ? 'Add Example' : 'Edit Example'"
    subtitle="Guided example help tune how the agent retrieves and responds to questions."
    :confirm-label="isNew ? 'Add Example' : 'Save Changes'"
    :disable-confirm="!isValid"
    size="md"
    @update:model-value="$emit('update:showDialog', $event)"
    @cancel="handleClose"
    @confirm="handleSave"
  >
    <!-- Example Label Section -->
    <kg-dialog-section
      title="Example Label"
      description="A short, descriptive name to identify this example."
      icon="label"
      icon-color="blue-7"
      focus-highlight
    >
      <km-input
        v-model="form.title"
        placeholder="e.g., Product return policy inquiry"
      />
    </kg-dialog-section>

    <!-- User Message Section -->
    <kg-dialog-section
      title="User Message"
      description="The question or message the user would send to the agent."
      icon="chat_bubble_outline"
      icon-color="teal-7"
      focus-highlight
    >
      <km-input
        v-model="form.input"
        type="textarea"
        autogrow
        rows="3"
        placeholder="What does your return policy cover? Can I return items purchased online?"
      />
    </kg-dialog-section>

    <!-- Agent Response Section -->
    <kg-dialog-section
      title="Agent Response"
      description="The expected response, including proper citations and tone."
      icon="smart_toy"
      icon-color="deep-purple-6"
      focus-highlight
    >
      <km-input
        v-model="form.output"
        type="textarea"
        autogrow
        rows="4"
        placeholder="Our return policy allows returns within 30 days of purchase for most items [1]. Online purchases can be returned either by mail or in-store [2]..."
      />
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
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
