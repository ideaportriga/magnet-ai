<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const { draft } = useEntityDetail('mcp_servers')
const route = useRoute()

const server = computed(() => draft.value)
const activeToolName = computed(() => route.params?.name || '')

const crumbs = computed(() => {
  const trail = [{ label: server.value?.name ?? '', to: server.value?.id ? `/mcp/${server.value.id}` : undefined }]
  if (activeToolName.value) trail.push({ label: activeToolName.value })
  return trail
})
</script>
