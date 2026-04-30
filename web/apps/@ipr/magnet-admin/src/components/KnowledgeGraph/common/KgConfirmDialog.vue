<template>
  <km-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <km-card class="kg-confirm-dialog" :style="dialogStyle">
      <!-- Header -->
      <div class="km-card-section kg-confirm-dialog__header">
        <div class="cluster" data-wrap="no" data-gap="xs">
          <div v-if="icon" class="kg-confirm-dialog__icon" :class="`kg-confirm-dialog__icon--${iconVariant}`">
            <km-glyph :name="icon" size="20px" />
          </div>
          <div class="flex-1 kg-confirm-dialog__title">{{ title }}</div>
          <km-btn icon="close" flat dense round size="sm" tone="weak" @click="$emit('update:modelValue', false)" />
        </div>
      </div>

      <!-- Description -->
      <div v-if="description || $slots.description" class="km-card-section kg-confirm-dialog__description">
        <span v-if="!$slots.description">{{ description }}</span>
        <slot name="file-text" />
      </div>

      <!-- Content (options, warnings, etc.) -->
      <div v-if="$slots.default" class="km-card-section kg-confirm-dialog__content">
        <slot />
      </div>

      <!-- Warning -->
      <div v-if="warning || $slots.warning" class="km-card-section kg-confirm-dialog__warning">
        <kg-warning-banner :variant="warningVariant">
          <slot name="warning">{{ warning }}</slot>
        </kg-warning-banner>
      </div>

      <!-- Actions -->
      <div class="km-card-actions kg-confirm-dialog__actions">
        <km-btn flat :label="cancelLabel" tone="weak" @click="$emit('update:modelValue', false)" />
        <div class="km-space" />
        <km-btn
          :label="confirmLabel"
          :variant="destructive ? 'danger' : 'primary'"
          :disable="disableConfirm"
          @click="$emit('confirm')"
        />
      </div>

      <km-inner-loading :showing="loading" />
    </km-card>
  </km-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import KgWarningBanner from './KgWarningBanner.vue'

interface Props {
  modelValue: boolean
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  warning?: string
  warningVariant?: 'warning' | 'error' | 'info'
  destructive?: boolean
  loading?: boolean
  disableConfirm?: boolean
  width?: string
  height?: string
  icon?: string
  iconVariant?: 'error' | 'warning' | 'info'
}

const props = withDefaults(defineProps<Props>(), {
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  warningVariant: 'warning',
  destructive: false,
  loading: false,
  disableConfirm: false,
  width: '460px',
  height: 'auto',
  iconVariant: 'error',
})

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
}>()

const dialogStyle = computed(() => ({
  width: props.width,
  minHeight: props.height === 'auto' ? undefined : props.height,
}))
</script>

<style scoped>
.kg-confirm-dialog {
  display: flex;
  flex-direction: column;
  padding: 24px;
  border-radius: var(--ds-radius-xl);
}

.kg-confirm-dialog__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 36px;
  block-size: 36px;
  min-inline-size: 36px;
  border-radius: var(--ds-radius-full);
}

.kg-confirm-dialog__icon--error {
  background: var(--ds-color-error-bg);
  color: var(--ds-color-error);
}

.kg-confirm-dialog__icon--warning {
  background: var(--ds-color-warning-bg);
  color: var(--ds-color-warning);
}

.kg-confirm-dialog__icon--info {
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
}

.kg-confirm-dialog__header,
.kg-confirm-dialog__description,
.kg-confirm-dialog__content,
.kg-confirm-dialog__warning {
  padding: 0 !important;
}

.kg-confirm-dialog__title {
  font-size: var(--ds-font-size-body-lg);
  font-weight: 600;
  line-height: 1.3;
  color: var(--ds-color-black);
}

.kg-confirm-dialog__description {
  margin-block-start: 14px;
  padding-inline-start: 2px !important;
  font-size: var(--ds-font-size-body);
  line-height: 1.5;
  color: var(--ds-color-secondary-text);
}

.kg-confirm-dialog__content {
  margin-block-start: 16px;
}

.kg-confirm-dialog__warning {
  margin-block-start: 16px;
}

.kg-confirm-dialog__actions {
  margin-block-start: 20px;
  padding: 0 !important;
  gap: 8px;
}
</style>
