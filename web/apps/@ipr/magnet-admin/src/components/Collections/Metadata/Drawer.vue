<template>
  <km-drawer-layout storage-key="drawer-collections-metadata" no-scroll>
    <template #header>
      <div class="cluster">
        <km-btn flat simple :label="`${m.common_back()} ${m.common_to()} ${m.common_preview()}`" icon-size="16px" icon="arrow-left" tone="subtle" @click="closeDrawer" />
      </div>
    </template>
    <div class="km-heading-4">{{ m.common_metadata() }}</div>
    <div class="mb-md">{{ m.collections_metadataExposureDesc() }}</div>
    <div class="cluster mt-lg" data-gap="lg">
      <div class="basis-12">
        <div class="cluster" data-align="baseline">
          <div class="flex-none mr-sm">
            <km-toggle v-model="enabled" dense />
          </div>
          <div class="flex-1">{{ m.common_enabled() }}</div>
        </div>
      </div>
      <div class="basis-12">
        <div class="km-field text-secondary-text pb-xs">{{ m.common_name() }}</div>
        <km-input v-model="name" />
        <div class="km-description text-secondary-text mt-xs pl-xs">{{ m.collections_metadataNameHint() }}</div>
      </div>
      <div class="basis-12">
        <div class="km-field text-secondary-text">{{ m.common_mapping() }}</div>
        <km-input v-model="mapping" type="textarea" autogrow />
        <div class="km-description text-secondary-text mt-xs pl-xs">{{ m.collections_metadataMappingHint() }}</div>
      </div>
      <div class="basis-12">
        <div class="km-field text-secondary-text">{{ m.common_description() }}</div>
        <km-input v-model="description" type="textarea" autogrow />
        <div class="km-description text-secondary-text mt-xs pl-xs">{{ m.collections_metadataDescriptionHint() }}</div>
      </div>
    </div>
  </km-drawer-layout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useCollectionMetadataStore } from '@/stores/entityDetailStores'

// States & Stores
const { draft, updateField } = useEntityDetail('collections')
const collectionMetadataStore = useCollectionMetadataStore()

const config = ref(null)

const closeDrawer = () => {
  collectionMetadataStore.setActiveMetadataConfig(null)
}

function updateMetadataConfigField(field, value) {
  const metadataConfig = [...(draft.value?.metadata_config || [])]
  const updatedConfig = metadataConfig.map((item) => {
    if (item.id === config.value.id) {
      return { ...item, [field]: value }
    }
    return item
  })
  config.value = { ...config.value, [field]: value }
  updateField('metadata_config', updatedConfig)
}

const enabled = computed({
  get() { return config.value?.enabled },
  set(value) { updateMetadataConfigField('enabled', value) },
})

const name = computed({
  get() { return config.value?.name },
  set(value) { updateMetadataConfigField('name', value) },
})

const mapping = computed({
  get() { return config.value?.mapping },
  set(value) { updateMetadataConfigField('mapping', value) },
})

const description = computed({
  get() { return config.value?.description },
  set(value) { updateMetadataConfigField('description', value) },
})

onMounted(() => {
  config.value = collectionMetadataStore.activeMetadataConfig
})

onUnmounted(() => {
  collectionMetadataStore.setActiveMetadataConfig(null)
})

watch(
  () => collectionMetadataStore.activeMetadataConfig,
  (newVal) => {
    config.value = newVal
  }
)
</script>
