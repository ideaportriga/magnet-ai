<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="kg-confirm-dialog" :style="dialogStyle">
      <!-- Header -->
      <q-card-section class="kg-confirm-dialog__header">
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">{{ title }}</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="$emit('update:modelValue', false)" />
          </div>
        </div>
      </q-card-section>

      <!-- Description -->
      <q-card-section v-if="description" class="kg-confirm-dialog__description">
        <div class="km-description text-secondary-text">
          <span v-if="!$slots.description" class="text-weight-medium">{{ description }}</span>
          <slot name="description" />
        </div>
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
        <div class="col-auto">
          <km-btn flat :label="cancelLabel" color="primary" @click="$emit('update:modelValue', false)" />
        </div>
        <div class="col" />
        <div class="col-auto">
          <km-btn
            :label="confirmLabel"
            :bg="destructive ? 'error-bg' : undefined"
            :hover-bg="destructive ? 'error-text' : undefined"
            :color="destructive ? 'error-text' : 'primary'"
            :loading="loading"
            :disable="disableConfirm"
            @click="$emit('confirm')"
          />
        </div>
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
}

const props = withDefaults(defineProps<Props>(), {
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  warningVariant: 'warning',
  destructive: false,
  loading: false,
  disableConfirm: false,
  width: '676px',
  height: 'auto',
})

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
}>()

const dialogStyle = computed(() => ({
  width: props.width,
  minHeight: props.height === 'auto' ? undefined : props.height,
  padding: '32px',
}))
</script>

<style scoped>
.kg-confirm-dialog {
  display: flex;
  flex-direction: column;
}

.kg-confirm-dialog__header,
.kg-confirm-dialog__description,
.kg-confirm-dialog__content,
.kg-confirm-dialog__warning {
  padding: 0 !important;
}

.kg-confirm-dialog__description {
  margin-top: 16px;
}

.kg-confirm-dialog__content {
  margin-top: 16px;
}

.kg-confirm-dialog__warning {
  margin-top: 24px;
}

.kg-confirm-dialog__actions {
  margin-top: auto;
  padding: 30px 0 0 0 !important;
}
</style>

