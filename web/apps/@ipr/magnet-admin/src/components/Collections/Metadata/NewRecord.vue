<template>
  <km-dialog :model-value="showNewDialog" @cancel="$emit('cancel')">
    <km-card class="card-style" style="min-inline-size: 800px">
      <div class="km-card-section card-section-style">
        <div class="cluster">
          <div class="flex-1">
            <div class="km-heading-7">{{ m.collections_newMetadataExposure() }}</div>
          </div>
          <div class="flex-none">
            <km-btn icon="close" flat dense @click="$emit('cancel')" />
          </div>
        </div>
      </div>
      <div class="km-card-section card-section-style mb-md">
        <div class="cluster bg-light full-width py-xs px-sm mb-lg" data-gap="sm" data-wrap="no">
          <km-glyph name="info" size="20px" style="min-inline-size: 20px" />
          <div class="km-paragraph">
            {{ m.collections_metadataExposureDesc() }}
          </div>
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-md">{{ m.common_name() }}</div>
        <div class="full-width">
          <km-input v-model="newRecord.name" height="30px" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-md">{{ m.common_mapping() }}</div>
        <div class="full-width">
          <km-input v-model="newRecord.mapping" height="30px" type="textarea" autogrow />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-md">{{ m.common_description() }}</div>
        <div class="full-width">
          <km-input v-model="newRecord.description" height="30px" type="textarea" autogrow />
        </div>
        <div class="cluster mt-lg">
          <div class="flex-none">
            <km-btn flat :label="m.common_cancel()" tone="brand" @click="$emit('cancel')" />
          </div>
          <div class="flex-1" />
          <div class="flex-none">
            <km-btn :label="m.common_create()" :disable="!newRecord.name || !newRecord.mapping" @click="create" />
          </div>
        </div>
      </div>
    </km-card>
  </km-dialog>
</template>

<script setup lang="ts">
import { onUnmounted, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useNotify } from '@/composables/useNotify'

// States & Stores
const { draft, updateField } = useEntityDetail('collections')

defineProps<{
  showNewDialog: boolean
}>()
const emit = defineEmits(['cancel'])

const { notifyError } = useNotify()

const newRecord = ref({
  id: crypto.randomUUID(),
  enabled: true,
  name: '',
  mapping: '',
  description: '',
})

onUnmounted(() => {
  emit('cancel')
})

const create = () => {
  const metadataConfig = [...(draft.value?.metadata_config || [])]
  const newName = (newRecord.value?.name || '').trim()
  const isDuplicate = metadataConfig.some((item) => (item?.name || '').trim() === newName)
  if (isDuplicate) {
    notifyError(m.validation_metadataFieldAlreadyExists({ name: newName }))
    return
  }
  metadataConfig.push(newRecord.value)
  updateField('metadata_config', metadataConfig)
  emit('cancel')
}
</script>
