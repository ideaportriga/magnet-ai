<template>
  <div class="kg-dialog-section" :style="sectionStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="kg-dialog-section__inner" :style="innerSectionStyle">
      <!-- Header -->
      <div class="kg-dialog-section__header" :style="headerStyle">
        <div class="cluster" data-gap="sm">
          <span v-if="icon" class="kg-dialog-section__icon" :style="iconStyle">
            <km-glyph :name="icon" size="18px" tone="current" />
          </span>
          <span class="km-heading-8 text-weight-medium">{{ title }}</span>
          <slot name="title-badge" />
        </div>
        <slot name="header-actions" />
      </div>

      <!-- Description -->
      <div v-if="description" class="kg-dialog-section__description">
        {{ description }}
      </div>

      <!-- Content -->
      <div class="kg-dialog-section__content" :class="{ 'kg-dialog-section__content--disabled': disabled }">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { resolveKgDialogToneColor, type KgDialogTone } from './kgDialogTone'

interface Props {
  title: string
  description?: string
  icon?: string
  tone?: KgDialogTone
  iconColor?: string
  borderColor?: string
  backgroundColor?: string
  focusHighlight?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  icon: '',
  tone: 'brand',
  borderColor: 'var(--ds-color-border)',
  backgroundColor: 'var(--ds-color-background)',
  description: '',
  focusHighlight: false,
  disabled: false,
})

const isFocused = ref(false)

const onFocusIn = () => {
  if (props.focusHighlight) isFocused.value = true
}

const onFocusOut = () => {
  if (props.focusHighlight) isFocused.value = false
}

const sectionAccentColor = computed(() => resolveKgDialogToneColor(props.tone, props.iconColor))

const iconStyle = computed(() => ({
  color: sectionAccentColor.value,
}))

const sectionStyle = computed(() => ({
  background: props.backgroundColor,
  border: `1px solid ${props.borderColor}`,
}))

const innerSectionStyle = computed(() => ({
  borderColor: isFocused.value ? sectionAccentColor.value : 'transparent',
}))

const headerStyle = computed(() => ({
  borderBottom: `1px solid ${props.borderColor}`,
}))
</script>

<style>
.kg-dialog-section {
  border-radius: var(--ds-radius-lg);
}

.kg-dialog-section__inner {
  border-radius: var(--ds-radius-lg);
  position: relative;
  margin: -1px;
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 16px;
}

.kg-dialog-section__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-block-end: 8px;
}

.kg-dialog-section__icon {
  display: inline-flex;
}

.kg-dialog-section__description {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  line-height: 1.4;
  margin-block: 4px 16px;
}

.kg-dialog-section__content--disabled {
  opacity: 0.5;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

/* Ensure form controls inside section have white background */
.kg-dialog-section .km-control,
.kg-dialog-section .km-select[data-state='open'] {
  background-color: var(--ds-color-white) !important;
}

.kg-dialog-section .km-input .ds-input,
.kg-dialog-section .km-input .ds-textarea {
  background-color: var(--ds-color-white) !important;
  border-color: var(--ds-color-control-border) !important;
  transition:
    border-color 600ms,
    background-color 600ms;
}
</style>

