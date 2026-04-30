<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePromptQueueStore } from '@/stores/promptQueueStore'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const pqStore = usePromptQueueStore()
const config = computed(() => pqStore.selectedPromptQueueConfig)
const configName = computed(() => config.value?.name ?? '')
const crumbs = computed(() => [{ label: configName.value }])
</script>
