<template>
  <q-dialog :model-value="showNewDialog" @cancel="$emit('cancel')">
    <q-card class="card-style" style="min-width: 800px">
      <q-card-section class="card-section-style">
        <div class="row">
          <div class="col">
            <div class="km-heading-7">New metadata exposure</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="$emit('cancel')" />
          </div>
        </div>
      </q-card-section>
      <q-card-section class="card-section-style q-mb-md">
        <div class="row bg-light full-width q-py-4 q-px-8 q-gap-8 no-wrap items-center q-mb-lg">
          <q-icon name="o_info" color="icon" size="20px" style="min-width: 20px" />
          <div class="km-paragraph">
            Configure how chunk metadata will be exposed for search and retrieval. To map metadata fields use JSONPath expression.
          </div>
        </div>
        <div class="km-field text-secondary-text q-pb-xs q-pl-8 q-mt-md">Name</div>
        <div class="full-width">
          <km-input v-model="newRecord.name" height="30px" />
        </div>
        <div class="km-field text-secondary-text q-pb-xs q-pl-8 q-mt-md">Mapping</div>
        <div class="full-width">
          <km-input v-model="newRecord.mapping" height="30px" type="textarea" autogrow />
        </div>
        <div class="km-field text-secondary-text q-pb-xs q-pl-8 q-mt-md">Description</div>
        <div class="full-width">
          <km-input v-model="newRecord.description" height="30px" type="textarea" autogrow />
        </div>
        <div class="row q-mt-lg">
          <div class="col-auto">
            <km-btn flat label="Cancel" color="primary" @click="$emit('cancel')" />
          </div>
          <div class="col" />
          <div class="col-auto">
            <km-btn label="Create" :disable="!newRecord.name || !newRecord.mapping" @click="create" />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar'
import { onUnmounted, ref } from 'vue'
import { useStore } from 'vuex'

// States & Stores
const store = useStore()

defineProps<{
  showNewDialog: boolean
}>()
const emit = defineEmits(['cancel'])

const $q = useQuasar()

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
  const metadataConfig = store.getters.knowledge?.metadata_config || []
  const newName = (newRecord.value?.name || '').trim()
  const isDuplicate = metadataConfig.some((item) => (item?.name || '').trim() === newName)
  if (isDuplicate) {
    $q.notify({
      position: 'top',
      message: `Metadata field ${newName} already exists`,
      color: 'negative',
      textColor: 'black',
      timeout: 1500,
    })
    return
  }
  metadataConfig.push(newRecord.value)
  store.dispatch('updateKnowledge', { metadata_config: metadataConfig })
  emit('cancel')
}
</script>
