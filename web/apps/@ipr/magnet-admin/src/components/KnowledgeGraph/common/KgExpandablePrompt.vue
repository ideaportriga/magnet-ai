<template>
  <div class="kg-expandable-prompt" :style="sectionStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="kg-expandable-prompt__inner" :style="innerSectionStyle">
      <q-expansion-item v-model="isExpanded" expand-icon-class="text-grey-6" dense>
        <template #header>
          <div class="kg-expandable-prompt__header">
            <q-avatar icon="format_quote" color="primary-light" text-color="primary" size="32px" font-size="18px" />
            <div class="kg-expandable-prompt__header-text">
              <span class="km-heading-8 text-weight-medium">{{ title }}</span>
              <span class="q-mt-2 text-secondary-text" style="font-size: 0.8rem">{{ description }}</span>
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
      </q-expansion-item>
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
  background: '#fafafa',
  border: `1px solid #c5cae9`,
}))

const innerSectionStyle = computed(() => ({
  borderColor: isFocused.value ? 'var(--q-primary)' : 'transparent',
}))
</script>

<style scoped>
.kg-expandable-prompt {
  border-radius: 6px;
}

.kg-expandable-prompt :deep(.q-expansion-item) {
  background: transparent;
}

.kg-expandable-prompt :deep(.q-item) {
  padding: 0;
  min-height: unset;
  background: linear-gradient(135deg, #f5f7ff 0%, #ffffff 100%);
  border-radius: 6px;
}

.kg-expandable-prompt :deep(.q-expansion-item__container) {
  background: transparent;
}

.kg-expandable-prompt__header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 16px 8px 12px;
  width: 100%;
  border-radius: 6px;
}

.kg-expandable-prompt:hover {
  border-color: var(--q-primary) !important;
}

.kg-expandable-prompt__header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kg-expandable-prompt__content {
  padding: 12px 16px 16px;
  border-top: 1px solid var(--section-border, #e0e0e0);
}

.kg-expandable-prompt__textarea :deep(.q-field__native) {
  font-size: 13px;
  line-height: 1.6;
  color: #37474f;
}

.kg-expandable-prompt__textarea :deep(.q-field__native::placeholder) {
  color: #b0bec5;
}

/* Expansion item styling overrides */
.kg-expandable-prompt :deep(.q-expansion-item__content) {
  background: transparent;
}

.kg-expandable-prompt :deep(.q-focus-helper) {
  display: none;
}

.kg-expandable-prompt__inner {
  border-radius: 6px;
  position: relative;
  margin: -1px -1px;
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.q-field__control:before) {
  border-radius: 6px !important;
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
</style>

