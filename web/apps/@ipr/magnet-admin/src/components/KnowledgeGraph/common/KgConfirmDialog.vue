<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="kg-confirm-dialog" :style="dialogStyle">
      <!-- Header -->
      <q-card-section class="kg-confirm-dialog__header">
        <div class="row items-center no-wrap q-gutter-x-sm">
          <div v-if="icon" class="kg-confirm-dialog__icon" :class="`kg-confirm-dialog__icon--${iconVariant}`">
            <q-icon :name="icon" size="20px" />
          </div>
          <div class="col kg-confirm-dialog__title">{{ title }}</div>
          <q-btn icon="close" flat dense round size="sm" color="grey-6" @click="$emit('update:modelValue', false)" />
        </div>
      </q-card-section>

      <!-- Description -->
      <q-card-section v-if="description || $slots.description" class="kg-confirm-dialog__description">
        <span v-if="!$slots.description">{{ description }}</span>
        <slot name="description" />
      </q-card-section>

      <!-- Content (options, warnings, etc.) -->
      <q-card-section v-if="$slots.default" class="kg-confirm-dialog__content">
        <slot />
      </q-card-section>

      <!-- Warning -->
      <q-card-section v-if="warning || $slots.warning" class="kg-confirm-dialog__warning">
        <kg-warning-banner :variant="warningVariant">
          <slot name="warning">{{ warning }}</slot>
        </kg-warning-banner>
      </q-card-section>

      <!-- Actions -->
      <q-card-actions class="kg-confirm-dialog__actions">
        <km-btn flat :label="cancelLabel" color="grey-7" @click="$emit('update:modelValue', false)" />
        <q-space />
        <km-btn
          :label="confirmLabel"
          :bg="destructive ? 'error-bg' : undefined"
          :hover-bg="destructive ? 'error-text' : undefined"
          :color="destructive ? 'error-text' : 'primary'"
          :loading="loading"
          :disable="disableConfirm"
          @click="$emit('confirm')"
        />
      </q-card-actions>

      <q-inner-loading :showing="loading" />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
  border-radius: 12px;
}

.kg-confirm-dialog__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: 50%;
}

.kg-confirm-dialog__icon--error {
  background: #fee2e2;
  color: #dc2626;
}

.kg-confirm-dialog__icon--warning {
  background: #fef3c7;
  color: #d97706;
}

.kg-confirm-dialog__icon--info {
  background: #dbeafe;
  color: #2563eb;
}

.kg-confirm-dialog__header,
.kg-confirm-dialog__description,
.kg-confirm-dialog__content,
.kg-confirm-dialog__warning {
  padding: 0 !important;
}

.kg-confirm-dialog__title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
  color: #111827;
}

.kg-confirm-dialog__description {
  margin-top: 14px;
  padding-left: 2px !important;
  font-size: 14px;
  line-height: 1.5;
  color: #4b5563;
}

.kg-confirm-dialog__content {
  margin-top: 16px;
}

.kg-confirm-dialog__warning {
  margin-top: 16px;
}

.kg-confirm-dialog__actions {
  margin-top: 20px;
  padding: 0 !important;
  gap: 8px;
}
</style>
