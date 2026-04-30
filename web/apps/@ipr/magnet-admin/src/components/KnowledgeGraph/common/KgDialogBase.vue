<template>
  <km-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <km-card class="kg-dialog" :class="dialogClass" :style="dialogStyle">
      <!-- Header -->
      <div class="km-card-section kg-dialog__header">
        <div class="cluster">
          <div class="flex-1">
            <div class="km-heading-7">{{ title }}</div>
            <div v-if="subtitle" class="kg-dialog__subtitle">{{ subtitle }}</div>
          </div>
          <div class="flex-none self-start">
            <km-btn icon="close" flat round dense @click="onClose" />
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="km-card-section kg-dialog__content">
        <div class="stack" data-gap="lg">
          <slot />
        </div>

        <!-- Error Banner -->
        <km-banner v-if="error" class="mt-md bg-negative text-white" rounded dense>
          {{ error }}
        </km-banner>
      </div>

      <!-- Footer slot (fixed, above actions) -->
      <div v-if="$slots.footer" class="kg-dialog__footer">
        <slot name="footer" />
      </div>

      <!-- Actions -->
      <div class="km-card-actions kg-dialog__actions">
        <km-btn v-if="showConfirm" :label="cancelLabel" flat tone="brand" @click="onCancel" />
        <div class="km-space" />
        <km-btn
          v-if="showConfirm"
          no-caps
          unelevated
          class="kg-dialog__action__button"
          :label="confirmLabel"
          :disable="disableConfirm || loading"
          :loading="loading"
          @click="$emit('confirm')"
        />
        <km-btn
          v-if="!showConfirm"
          no-caps
          unelevated
          class="kg-dialog__action__button"
          :label="cancelLabel"
          @click="onCancel"
        />
      </div>

      <km-inner-loading :showing="innerLoading" />
    </km-card>
  </km-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

export type DialogSize = 'sm' | 'md' | 'lg' | 'xl'

interface Props {
  modelValue: boolean
  title: string
  subtitle?: string
  confirmLabel?: string
  cancelLabel?: string
  showConfirm?: boolean
  disableConfirm?: boolean
  loading?: boolean
  innerLoading?: boolean
  error?: string
  size?: DialogSize
  height?: string
  maxHeight?: string
}

const props = withDefaults(defineProps<Props>(), {
  confirmLabel: 'Save',
  cancelLabel: 'Cancel',
  showConfirm: true,
  disableConfirm: false,
  loading: false,
  innerLoading: false,
  error: '',
  size: 'md',
  height: '',
  maxHeight: '80vh',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'cancel'): void
  (e: 'confirm'): void
  (e: 'close'): void
}>()

const sizeMap: Record<DialogSize, { min: string; max: string }> = {
  sm: { min: '580px', max: '580px' },
  md: { min: '720px', max: '720px' },
  lg: { min: '900px', max: '900px' },
  xl: { min: '1000px', max: '1000px' },
}

const dialogStyle = computed(() => {
  const { min, max } = sizeMap[props.size]
  const style: Record<string, string> = {
    minWidth: min,
    maxWidth: max,
    display: 'flex',
    flexDirection: 'column',
  }
  if (props.height) {
    style.height = props.height
  }
  if (props.maxHeight) {
    style.maxHeight = props.maxHeight
  }
  return style
})

const dialogClass = computed(() => ({}))

const onCancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}

const onClose = () => {
  emit('close')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.kg-dialog {
  padding: 8px;
}

.kg-dialog__header {
  padding-block-end: 16px;
  flex-shrink: 0;
}

.kg-dialog__subtitle {
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-label);
  font-weight: 400;
  line-height: 1.4;
  margin-block: 4px;
}

.kg-dialog__content {
  padding: 0 16px;
  flex: 1 1 auto;
  overflow-block: auto;
  min-block-size: 0;
}

.kg-dialog__footer {
  flex-shrink: 0;
  padding: 16px 16px 0;
}

.kg-dialog__actions {
  padding: 16px;
  flex-shrink: 0;
}

.kg-dialog__action__button {
  font-family: var(--font-default) !important;
  block-size: 34px !important;
  min-block-size: 34px !important;
  padding-inline: 12px;
}
</style>
