<template>
  <div class="kg-expandable-prompt" :style="sectionStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="kg-expandable-prompt__inner" :style="innerSectionStyle">
      <km-expansion-item v-model="isExpanded" expand-icon-class="text-grey-6" dense>
        <template #header>
          <div class="kg-expandable-prompt__header">
            <km-avatar icon="format_quote" tone="brand-soft" size="32px" font-size="18px" />
            <div class="kg-expandable-prompt__header-text">
              <span class="km-heading-8 text-weight-medium">{{ title }}</span>
              <span class="mt-2xs text-secondary-text km-caption">{{ description }}</span>
            </div>
          </div>
        </template>

        <div class="kg-expandable-prompt__content">
          <km-input
            :model-value="modelValue"
            type="textarea"
            autogrow
            rows="4"
            :placeholder="placeholder"
            class="kg-expandable-prompt__textarea"
            input-class="font-mono text-body2"
            @update:model-value="$emit('update:modelValue', $event)"
          />
        </div>
      </km-expansion-item>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

defineProps<{
  modelValue: string
  title: string
  description?: string
  placeholder?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: string | number | null): void
}>()

const isExpanded = ref(false)
const isFocused = ref(false)

const onFocusIn = () => {
  isFocused.value = true
}

const onFocusOut = () => {
  isFocused.value = false
}

const sectionStyle = computed(() => ({
  background: 'var(--ds-color-background)',
  border: `1px solid var(--ds-color-primary-light)`,
}))

const innerSectionStyle = computed(() => ({
  borderColor: isFocused.value ? 'var(--ds-color-primary)' : 'transparent',
}))
</script>

<style>
.kg-expandable-prompt {
  border-radius: var(--ds-radius-md);
}

.kg-expandable-prompt .km-expansion-item {
  background: transparent;
}

.kg-expandable-prompt .km-expansion-item__trigger {
  padding: 0;
  min-block-size: unset;
  background: linear-gradient(135deg, var(--ds-color-primary-bg) 0%, var(--ds-color-white) 100%);
  border-radius: var(--ds-radius-md);
}

.kg-expandable-prompt .km-expansion-item__trigger:hover {
  background: linear-gradient(135deg, var(--ds-color-primary-bg) 0%, var(--ds-color-white) 100%);
}

.kg-expandable-prompt .km-expansion-item__item {
  background: transparent;
}

.kg-expandable-prompt__header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 16px 8px 12px;
  inline-size: 100%;
  border-radius: var(--ds-radius-md);
}

.kg-expandable-prompt:hover {
  border-color: var(--ds-color-primary) !important;
}

.kg-expandable-prompt__header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kg-expandable-prompt__content {
  padding: 12px 16px 16px;
  border-block-start: 1px solid var(--section-border, var(--ds-color-border));
}

.kg-expandable-prompt__textarea .ds-textarea {
  font-size: var(--ds-font-size-label);
  line-height: 1.6;
  color: var(--ds-color-secondary);
  border-radius: var(--ds-radius-md) !important;
}

.kg-expandable-prompt__textarea .ds-textarea::placeholder {
  color: var(--ds-color-border-2);
}

/* Expansion item styling overrides */
.kg-expandable-prompt .km-expansion-item__content-inner {
  background: transparent;
}

.kg-expandable-prompt__inner {
  border-radius: var(--ds-radius-md);
  position: relative;
  margin: -1px;
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
}

.kg-expandable-prompt__textarea .ds-textarea:focus-visible {
  background: var(--ds-color-white) !important;
  box-shadow: none;
}

.kg-expandable-prompt__textarea .ds-textarea:hover {
  border-color: var(--ds-color-control-border) !important;
}

.kg-expandable-prompt__textarea {
  margin: 0px -12px -12px !important;
}

.kg-expandable-prompt__textarea textarea {
  margin: 6px 4px !important;
}
</style>

