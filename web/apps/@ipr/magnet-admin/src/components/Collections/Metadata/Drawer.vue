<template lang="pug">
km-drawer-layout(storageKey="drawer-collections-metadata", noScroll)
  template(#header)
    .row.items-center
      km-btn(flat, simple, :label='`Back to Preview`', iconSize='16px', icon='fas fa-arrow-left', @click='closeDrawer', color='secondary-text')
    .km-heading-4 Metadata exposure
  .q-mb-md Configure how chunk metadata will be exposed for search and retrieval. To map metadata fields use JSONPath expression.
  .row.q-gap-16.q-mt-lg
    .col-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='enabled', dense)
        .col Enable
    .col-12
      .km-field.text-secondary-text.q-pb-xs Name
      km-input(v-model='name')
      .km-description.text-secondary-text.q-mt-xs.q-pl-4
        | Any clear and concise name, that will be used as a reference across the system.
    .col-12
      .km-field.text-secondary-text Mapping
      km-input(v-model='mapping', type='textarea', autogrow)
      .km-description.text-secondary-text.q-mt-xs.q-pl-4 Any valid JSONPath expression.
    .col-12
      .km-field.text-secondary-text Description
      km-input(v-model='description', type='textarea', autogrow)
      .km-description.text-secondary-text.q-mt-xs.q-pl-4 Clear description, that can be easily understood by both humans and AI agents.
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useCollectionDetailStore, useCollectionMetadataStore } from '@/stores/entityDetailStores'

// States & Stores
const collectionStore = useCollectionDetailStore()
const collectionMetadataStore = useCollectionMetadataStore()

const config = ref(null)

const closeDrawer = () => {
  collectionMetadataStore.setActiveMetadataConfig(null)
}

const enabled = computed({
  get() {
    return config.value?.enabled
  },
  set(value) {
    const metadataConfig = collectionStore.entity?.metadata_config || []
    metadataConfig.forEach((item) => {
      if (item.id === config.value.id) {
        item.enabled = value
        config.value.enabled = value
      }
    })
  },
})

const name = computed({
  get() {
    return config.value?.name
  },
  set(value) {
    const metadataConfig = collectionStore.entity?.metadata_config || []
    metadataConfig.forEach((item) => {
      if (item.id === config.value.id) {
        item.name = value
        config.value.name = value
      }
    })
  },
})

const mapping = computed({
  get() {
    return config.value?.mapping
  },
  set(value) {
    const metadataConfig = collectionStore.entity?.metadata_config || []
    metadataConfig.forEach((item) => {
      if (item.id === config.value.id) {
        item.mapping = value
        config.value.mapping = value
      }
    })
  },
})

const description = computed({
  get() {
    return config.value?.description
  },
  set(value) {
    const metadataConfig = collectionStore.entity?.metadata_config || []
    metadataConfig.forEach((item) => {
      if (item.id === config.value.id) {
        item.description = value
        config.value.description = value
      }
    })
  },
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
