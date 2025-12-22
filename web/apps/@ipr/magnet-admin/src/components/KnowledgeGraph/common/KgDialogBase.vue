<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="kg-dialog" :class="dialogClass" :style="dialogStyle">
      <!-- Header -->
      <q-card-section class="kg-dialog__header">
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">{{ title }}</div>
            <div v-if="subtitle" class="kg-dialog__subtitle">{{ subtitle }}</div>
          </div>
          <div class="col-auto self-start">
            <q-btn icon="close" flat round dense @click="onClose" />
          </div>
        </div>
      </q-card-section>

      <!-- Content -->
      <q-card-section class="kg-dialog__content" :class="contentClass">
        <div class="column q-gap-16">
          <slot />
        </div>

        <!-- Error Banner -->
        <q-banner v-if="error" class="q-mt-md bg-negative text-white" rounded dense>
          {{ error }}
        </q-banner>
      </q-card-section>

      <!-- Actions -->
      <q-card-actions class="kg-dialog__actions">
        <km-btn :label="cancelLabel" flat color="primary" @click="onCancel" />
        <q-space />
        <q-btn
          no-caps
          unelevated
          color="primary"
          class="kg-dialog__action__button"
          :label="confirmLabel"
          :disable="disableConfirm || loading"
          :loading="loading"
          @click="$emit('confirm')"
        />
      </q-card-actions>

      <q-inner-loading :showing="innerLoading" />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type DialogSize = 'sm' | 'md' | 'lg' | 'xl'

interface Props {
  modelValue: boolean
  title: string
  subtitle?: string
  confirmLabel?: string
  cancelLabel?: string
  disableConfirm?: boolean
  loading?: boolean
  innerLoading?: boolean
  error?: string
  size?: DialogSize
  scrollable?: boolean
  maxHeight?: string
}

const props = withDefaults(defineProps<Props>(), {
  confirmLabel: 'Save',
  cancelLabel: 'Cancel',
  disableConfirm: false,
  loading: false,
  innerLoading: false,
  error: '',
  size: 'md',
  scrollable: false,
  maxHeight: '',
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
  }
  if (props.scrollable && props.maxHeight) {
    style.maxHeight = props.maxHeight
    style.display = 'flex'
    style.flexDirection = 'column'
  }
  return style
})

const dialogClass = computed(() => ({
  'kg-dialog--scrollable': props.scrollable,
}))

const contentClass = computed(() => ({
  'kg-dialog__content--scrollable': props.scrollable,
}))

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
  padding-bottom: 0;
}

.kg-dialog__subtitle {
  font-size: 14px;
  color: #6b6b6b;
  font-weight: 400;
  line-height: 1.4;
  margin-top: 4px;
  margin-bottom: 4px;
}

.kg-dialog__content {
  padding: 16px;
}

.kg-dialog__content--scrollable {
  flex: 1 1 auto;
  overflow: auto;
}

.kg-dialog__actions {
  padding: 16px;
}

.kg-dialog__action__button {
  font-size: 13px;
  font-family: var(--font-default) !important;
  height: 34px !important;
  min-height: 34px !important;
  padding-left: 12px;
  padding-right: 12px;
}
</style>
