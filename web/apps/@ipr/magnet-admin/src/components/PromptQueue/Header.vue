<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ configName }}
</template>

<script setup>
import { computed } from 'vue'
import { usePromptQueueStore } from '@/stores/promptQueueStore'

const pqStore = usePromptQueueStore()
const config = computed(() => pqStore.selectedPromptQueueConfig)
const configName = computed(() => config.value?.name ?? '')
</script>
