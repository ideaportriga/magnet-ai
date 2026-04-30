<template>
  <!-- Section variant (original behavior) -->
  <kg-dialog-section
    v-if="variant === 'section'"
    :title="title"
    :description="description"
    :icon="icon"
    :tone="tone"
    :background-color="backgroundColor"
    v-bind="sectionLegacyToneProps"
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
  </kg-dialog-section>

  <!-- Field variant (collapsible inline field) -->
  <div v-else class="kg-prompt-field" :style="fieldContainerStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="kg-prompt-field__inner" :style="innerSectionStyle">
      <!-- Collapsible field -->
      <km-expansion-item
        v-if="collapse"
        v-model="isExpanded"
        class="kg-prompt-field__expansion"
        header-class="kg-prompt-field__header"
        expand-icon-class="text-primary"
        dense
      >
        <template #header>
          <div class="cluster gap-x-xs">
            <span class="kg-prompt-field__icon" :style="iconStyle">
              <km-glyph :name="icon" size="16px" tone="current" />
            </span>
            <span class="km-input-label">{{ title }}</span>
          </div>
        </template>
        <div class="pt-sm">
          <km-input v-model="localValue" type="textarea" outlined autogrow :placeholder="placeholder" class="kg-prompt-field__textarea" />
        </div>
      </km-expansion-item>

      <!-- Non-collapsible field -->
      <div v-else class="kg-prompt-field__static">
        <div class="cluster mb-sm gap-x-xs">
          <span class="kg-prompt-field__icon" :style="iconStyle">
            <km-glyph :name="icon" size="16px" tone="current" />
          </span>
          <span class="km-input-label">{{ title }}</span>
        </div>
        <km-input v-model="localValue" type="textarea" outlined autogrow :placeholder="placeholder" class="kg-prompt-field__textarea" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { resolveKgDialogToneColor, type KgDialogTone } from './kgDialogTone'

interface Props {
  modelValue: string
  title: string
  description?: string
  placeholder?: string
  icon?: string
  tone?: KgDialogTone
  iconColor?: string
  borderColor?: string
  backgroundColor?: string
  variant?: 'section' | 'field'
  collapse?: boolean
  expanded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  icon: 'format_quote',
  tone: 'brand',
  variant: 'section',
  borderColor: 'var(--ds-color-border)',
  backgroundColor: 'var(--ds-color-background)',
  collapse: false,
  expanded: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:expanded', value: boolean): void
}>()

// Local expanded state - synced with prop
const isExpanded = ref(props.expanded)

const fieldContainerStyle = computed(() => ({
  background: props.backgroundColor,
  border: `1px solid ${props.borderColor}`,
}))

const sectionAccentColor = computed(() => resolveKgDialogToneColor(props.tone, props.iconColor))

const iconStyle = computed(() => ({
  color: sectionAccentColor.value,
}))

const sectionLegacyToneProps = computed(() => (props.iconColor ? { iconColor: props.iconColor } : undefined))

const innerSectionStyle = computed(() => ({
  borderColor: isFocused.value ? sectionAccentColor.value : 'transparent',
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

// Computed for v-model on q-input
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

<style>
/* Section variant styles */
.output-textarea .ds-textarea {
  border-radius: var(--ds-radius-lg) !important;
  background: var(--ds-color-white) !important;
}

.output-textarea .ds-textarea:hover {
  border-color: var(--ds-color-control-border) !important;
}

.output-textarea {
  margin: 0px -12px -12px !important;
}

.output-textarea textarea {
  margin: 6px 4px !important;
}

/* Field variant styles */
.kg-prompt-field {
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  overflow: hidden;
  position: relative;
}

.kg-prompt-field__inner {
  border-radius: var(--ds-radius-md);
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
}

.kg-prompt-field__expansion {
  overflow: hidden;
  border-radius: var(--ds-radius-md);
}

.kg-prompt-field__expansion .km-expansion-item__item {
  border: none;
}

.kg-prompt-field__expansion .kg-prompt-field__header {
  padding: 12px 16px;
  min-block-size: 48px;
  background: var(--ds-color-background);
  inline-size: 100%;
  display: flex;
  justify-content: space-between;
}

.kg-prompt-field__expansion .km-expansion-item__content-inner {
  padding: 0 16px 16px;
}

.kg-prompt-field__expansion .km-expansion-item__chevron {
  margin-inline-start: var(--ds-space-sm);
}

.kg-prompt-field__static {
  padding: 12px 16px 16px;
  background: var(--ds-color-background);
}

.kg-prompt-field__icon {
  display: inline-flex;
}

.kg-prompt-field__textarea {
  margin: 0px -12px -12px !important;
}

.kg-prompt-field__textarea .ds-textarea {
  background: var(--ds-color-white);
  border-radius: var(--ds-radius-md) !important;
  padding: 0;
  border: 1px solid var(--ds-color-control-border) !important;
}

.kg-prompt-field__textarea .ds-textarea:hover,
.kg-prompt-field__textarea .ds-textarea:focus-visible {
  border-color: var(--ds-color-border-2);
  border-width: 1px;
  box-shadow: none;
}

.kg-prompt-field__textarea textarea {
  padding: 5px 12px 0;
  line-height: 1.6;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  resize: none;
  overflow: hidden;
}

.kg-prompt-field__textarea textarea::placeholder {
  color: var(--ds-color-icon);
}
</style>
