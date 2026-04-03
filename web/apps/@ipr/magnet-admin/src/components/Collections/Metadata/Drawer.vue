<template lang="pug">
km-drawer-layout(storageKey="drawer-collections-metadata", noScroll)
  template(#header)
    .row.items-center
      km-btn(flat, simple, :label='`${m.common_back()} ${m.common_to()} ${m.common_preview()}`', iconSize='16px', icon='fas fa-arrow-left', @click='closeDrawer', color='secondary-text')
  .km-heading-4 {{ m.common_metadata() }}
  .q-mb-md {{ m.collections_metadataExposureDesc() }}
  .row.q-gap-16.q-mt-lg
    .col-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='enabled', dense)
        .col {{ m.common_enabled() }}
    .col-12
      .km-field.text-secondary-text.q-pb-xs {{ m.common_name() }}
      km-input(v-model='name')
      .km-description.text-secondary-text.q-mt-xs.q-pl-4
        | {{ m.collections_metadataNameHint() }}
    .col-12
      .km-field.text-secondary-text {{ m.common_mapping() }}
      km-input(v-model='mapping', type='textarea', autogrow)
      .km-description.text-secondary-text.q-mt-xs.q-pl-4 {{ m.collections_metadataMappingHint() }}
    .col-12
      .km-field.text-secondary-text {{ m.common_description() }}
      km-input(v-model='description', type='textarea', autogrow)
      .km-description.text-secondary-text.q-mt-xs.q-pl-4 {{ m.collections_metadataDescriptionHint() }}
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
