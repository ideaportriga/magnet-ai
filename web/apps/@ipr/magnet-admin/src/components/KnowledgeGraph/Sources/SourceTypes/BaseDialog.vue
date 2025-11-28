<template>
  <q-dialog v-model="dialogOpen">
    <q-card class="q-px-md q-py-sm" style="width: 600px; display: flex; flex-direction: column">
      <q-card-section>
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">{{ title }}</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="onCancel" />
          </div>
        </div>
      </q-card-section>

      <q-card-section>
        <slot />
        <q-banner v-if="error" class="q-mt-md bg-negative text-white" rounded dense>
          {{ error }}
        </q-banner>
      </q-card-section>

      <q-card-actions class="q-py-lg q-pr-lg">
        <km-btn label="Cancel" flat color="primary" @click="onCancel" />
        <q-space />
        <km-btn :label="confirmLabel" :disable="disableConfirm || loading" :loading="loading" @click="$emit('confirm')" />
      </q-card-actions>

      <q-inner-loading :showing="loading" />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  showDialog: boolean
  title: string
  confirmLabel: string
  disableConfirm?: boolean
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'confirm'): void
}>()

const dialogOpen = computed({
  get: () => props.showDialog,
  set: (v: boolean) => emit('update:showDialog', v),
})

const onCancel = () => {
  emit('cancel')
  emit('update:showDialog', false)
}
</script>
