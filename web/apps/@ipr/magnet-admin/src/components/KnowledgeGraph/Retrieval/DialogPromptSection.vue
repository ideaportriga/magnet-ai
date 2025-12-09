<template>
  <!-- Section variant (original behavior) -->
  <dialog-section
    v-if="variant === 'section'"
    :title="title"
    :description="description"
    :icon="icon"
    :color="color"
    :border-color="borderColor"
    :background-color="backgroundColor"
    focus-highlight
  >
    <km-input
      :model-value="modelValue"
      type="textarea"
      autogrow
      rows="2"
      :placeholder="placeholder"
      class="output-textarea"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </dialog-section>

  <!-- Field variant (collapsible inline field) -->
  <div v-else class="field-container" :style="fieldContainerStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="field-inner" :style="innerSectionStyle">
      <!-- Collapsible field -->
      <q-expansion-item
        v-if="collapse"
        v-model="isExpanded"
        class="field-expansion"
        header-class="field-header"
        expand-icon-class="text-primary"
        dense
      >
        <template #header>
          <div class="row items-center q-gutter-x-xs">
            <q-icon :name="icon" size="16px" color="primary" />
            <span class="km-input-label">{{ title }}</span>
          </div>
        </template>
        <div class="q-pt-sm">
          <q-input v-model="localValue" type="textarea" outlined autogrow :placeholder="placeholder" class="field-textarea" />
        </div>
      </q-expansion-item>

      <!-- Non-collapsible field -->
      <div v-else class="field-static">
        <div class="row items-center q-gutter-x-xs q-mb-sm">
          <q-icon :name="icon" size="16px" color="primary" />
          <span class="km-input-label">{{ title }}</span>
        </div>
        <q-input v-model="localValue" type="textarea" outlined autogrow :placeholder="placeholder" class="field-textarea" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { colors } from 'quasar'
import { computed, ref, watch } from 'vue'
import DialogSection from './DialogSection.vue'

interface Props {
  modelValue: string
  title: string
  description?: string
  placeholder?: string
  icon?: string
  color?: string
  borderColor?: string
  backgroundColor?: string
  variant?: 'section' | 'field'
  collapse?: boolean
  expanded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  icon: 'format_quote',
  variant: 'section',
  color: 'primary',
  borderColor: '#e8e8e8',
  backgroundColor: '#fafafa',
  collapse: false,
  expanded: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:expanded', value: boolean): void
}>()

const { getPaletteColor } = colors

// Local expanded state - synced with prop
const isExpanded = ref(props.expanded)

const fieldContainerStyle = computed(() => ({
  background: props.backgroundColor,
  border: `1px solid ${props.borderColor}`,
}))

const innerSectionStyle = computed(() => ({
  borderColor: isFocused.value ? getPaletteColor(props.color) : 'transparent',
}))

watch(
  () => props.expanded,
  (newVal) => {
    isExpanded.value = newVal
  }
)

watch(isExpanded, (newVal) => {
  emit('update:expanded', newVal)
})

// Computed for v-model on q-input (since q-input doesn't use update:modelValue the same way)
const localValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

// Focus tracking for field variant
const isFocused = ref(false)

const onFocusIn = () => {
  isFocused.value = true
}

const onFocusOut = () => {
  isFocused.value = false
}
</script>

<style scoped>
/* Section variant styles */
:deep(.q-field__control:before) {
  border-radius: 8px !important;
}

:deep(.km-input:not(.q-field--readonly).q-field--outlined.q-field--highlighted .q-field__control::before) {
  background: white !important;
}

:deep(.km-input:not(.q-field--readonly) .q-field__control:hover::before) {
  border-color: var(--q-control-border) !important;
}

:deep(.q-field--outlined .q-field__control:after) {
  border: none !important;
}

:deep(.km-input) {
  margin: 0px -12px -12px -12px !important;
}

:deep(textarea) {
  margin: 6px 4px !important;
}

/* Field variant styles */
.field-container {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.field-inner {
  border-radius: 6px;
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
}

.field-expansion {
  overflow: hidden;
  border-radius: 6px;
}

.field-expansion :deep(.q-expansion-item__container) {
  border: none;
}

.field-expansion :deep(.field-header) {
  padding: 12px 16px;
  min-height: 48px;
  background: #fafafa;
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.field-expansion :deep(.q-expansion-item__content) {
  padding: 0 16px 16px;
}

.field-expansion :deep(.q-item__section--side) {
  padding-right: 0;
}

.field-static {
  padding: 12px 16px 16px;
  background: #fafafa;
}

.field-textarea :deep(.q-field__control) {
  background: white;
  border-radius: 6px !important;
  padding: 0;
  /* margin: 0px -12px -12px -12px !important; */
}

.field-textarea :deep(.q-field__control::before) {
  border: 1px solid var(--q-control-border) !important;
  border-radius: 6px !important;
  background: white !important;
  margin: 0px -12px -12px -12px !important;
}

.field-textarea :deep(.q-field__control:hover::before) {
  border-color: #b0b0b0;
}

.field-textarea :deep(.q-field--focused .q-field__control::before) {
  border-color: #d0d7de;
  border-width: 1px;
}

.field-textarea :deep(.q-field--focused .q-field__control::after) {
  display: none;
}

.field-textarea :deep(textarea) {
  padding: 5px 12px 0 12px;
  line-height: 1.6;
  font-size: 13px;
  color: #24292f;
  resize: none;
  overflow: hidden;
}

.field-textarea :deep(textarea::placeholder) {
  color: #8b949e;
}

.field-textarea :deep(.q-field__marginal) {
  height: auto;
}

.field-textarea :deep(.q-focus-helper) {
  display: none;
}
</style>
