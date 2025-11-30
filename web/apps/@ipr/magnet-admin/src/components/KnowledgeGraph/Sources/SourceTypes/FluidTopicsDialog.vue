<template>
  <base-dialog
    :show-dialog="dialogOpen"
    :title="isEditMode ? 'Edit Fluid Topics Source' : 'Add Fluid Topics Source'"
    :confirm-label="isEditMode ? 'Save' : 'Add'"
    :disable-confirm="true"
    :loading="false"
    :error="error"
    @update:show-dialog="onModelUpdate"
    @cancel="onCancel"
  >
    <div class="column q-mt-xl q-mb-md items-center justify-center" style="text-align: center">
      <q-icon name="warning" color="orange-8" size="56px" class="q-mb-md" />
      <div class="km-heading-6 text-bold text-orange-9 q-mb-xs">Coming Soon</div>
      <div class="km-description text-secondary-text q-mt-xs" style="font-size: 17px">
        Fluid Topics integration is not yet implemented.
        <br />
        <span class="text-weight-medium">Please check back later.</span>
      </div>
    </div>
  </base-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import BaseDialog from './BaseDialog.vue'

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: any | null
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
}>()

const error = ref('')
const isEditMode = computed(() => !!props.source)

const dialogOpen = computed(() => props.showDialog)
const onModelUpdate = (v: boolean) => {
  if (!v) {
    emit('cancel')
  } else {
    emit('update:showDialog', v)
  }
}
const onCancel = () => {
  emit('cancel')
}
</script>
