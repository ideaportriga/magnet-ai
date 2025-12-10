<template>
  <q-dialog :model-value="showDialog" @update:model-value="$emit('update:showDialog', $event)">
    <q-card class="example-dialog q-pa-sm">
      <!-- Header -->
      <q-card-section>
        <div class="row items-center">
          <div class="col row items-center no-wrap q-gutter-x-sm">
            <div class="km-heading-7">{{ isNew ? 'Add Example' : 'Edit Example' }}</div>
          </div>
          <q-btn icon="close" flat round dense color="grey-6" @click="handleClose" />
        </div>
        <div class="km-description text-secondary-text q-mt-sm">
          Guided example help tune how the agent retrieves and responds to questions.
        </div>
      </q-card-section>

      <q-card-section class="column q-gap-16 q-pa-md">
        <!-- Example Label Section -->
        <dialog-section
          title="Example Label"
          description="A short, descriptive name to identify this example."
          icon="label"
          color="blue-7"
          focus-highlight
        >
          <km-input
            v-model="form.title"
            placeholder="e.g., Product return policy inquiry"
            class="section-input"
          />
        </dialog-section>

        <!-- User Message Section -->
        <dialog-section
          title="User Message"
          description="The question or message the user would send to the agent."
          icon="chat_bubble_outline"
          color="teal-7"
          focus-highlight
        >
          <km-input
            v-model="form.input"
            type="textarea"
            autogrow
            rows="3"
            placeholder="What does your return policy cover? Can I return items purchased online?"
            class="section-textarea"
          />
        </dialog-section>

        <!-- Agent Response Section -->
        <dialog-section
          title="Agent Response"
          description="The expected response, including proper citations and tone."
          icon="smart_toy"
          color="deep-purple-6"
          focus-highlight
        >
          <km-input
            v-model="form.output"
            type="textarea"
            autogrow
            rows="4"
            placeholder="Our return policy allows returns within 30 days of purchase for most items [1]. Online purchases can be returned either by mail or in-store [2]..."
            class="section-textarea"
          />
        </dialog-section>
      </q-card-section>

      <!-- Footer -->
      <q-card-actions class="q-pa-md">
        <km-btn label="Cancel" flat color="primary" @click="handleClose" />
        <q-space />
        <km-btn :label="isNew ? 'Add Example' : 'Save Changes'" :disable="!isValid" @click="handleSave" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import DialogSection from './DialogSection.vue'
import type { RetrievalExample } from './models'

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

<style scoped>
.example-dialog {
  min-width: 720px;
  max-width: 720px;
}

.section-input :deep(.q-field__control) {
  background: white;
}

.section-input :deep(.q-field__control::before) {
  border-radius: 6px !important;
}

.section-textarea :deep(.q-field__control) {
  background: white;
}

.section-textarea :deep(.q-field__control::before) {
  border-radius: 6px !important;
}

.section-textarea :deep(textarea) {
  line-height: 1.6;
}

/* Override for inputs inside dialog sections */
:deep(.dialog-section .km-input) {
  margin: 0 !important;
}

:deep(.dialog-section .km-input .q-field__control) {
  background: white !important;
}

:deep(.dialog-section .km-input:not(.q-field--readonly).q-field--outlined .q-field__control::before) {
  background: white !important;
}

:deep(.dialog-section .km-input:not(.q-field--readonly) .q-field__control:hover::before) {
  border-color: #b0bec5 !important;
}
</style>

