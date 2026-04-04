<template>
  <kg-dialog-base
    :model-value="dialogOpen"
    :title="m.knowledgeGraph_apiIngestSource()"
    :show-confirm="false"
    :cancel-label="m.common_close()"
    size="md"
    @update:model-value="onModelUpdate"
    @cancel="onCancel"
  >
    <kg-dialog-section :title="m.knowledgeGraph_sourceName()" :description="m.knowledgeGraph_sourceNameDesc()" icon="edit">
      <km-input v-model="sourceName" height="36px" readonly />
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { KgDialogBase, KgDialogSection } from '../../common'
import type { SourceRow } from '../models'

const props = defineProps<{
  showDialog: boolean
  source?: SourceRow | null
}>()

const emit = defineEmits<{
  cancel: []
}>()

const sourceName = ref('')

const dialogOpen = computed(() => props.showDialog)

watch(
  () => props.source,
  (newSource) => {
    if (newSource) {
      sourceName.value = newSource.name
    } else {
      sourceName.value = ''
    }
  },
  { immediate: true }
)

const onModelUpdate = (v: boolean) => {
  if (!v) emit('cancel')
}

const onCancel = () => {
  emit('cancel')
}
</script>
