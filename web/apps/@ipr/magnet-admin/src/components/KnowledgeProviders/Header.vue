<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ server?.name }}
</template>
<script setup>
import { computed } from 'vue'
import { useProviderDetailStore } from '@/stores/entityDetailStores'

const providerStore = useProviderDetailStore()
const server = computed(() => providerStore.entity)
</script>
