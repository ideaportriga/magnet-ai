<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useEntityDetail } from '@/composables/useEntityDetail'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const route = useRoute()
const { draft } = useEntityDetail('ai_apps')
const { options: items } = useCatalogOptions('ai_apps')

const activeRagId = computed(() => route.params.id)
const activeAIAppDB = computed(() => items.value.find((item) => item.id == activeRagId.value))
const activeRagName = computed(() => activeAIAppDB.value?.name)
const activeTabName = computed(() => {
  if (!route.params?.tab) return ''
  const tab = draft.value?.tabs?.find((t) => t.system_name === route.params.tab)
  return tab?.name || route.params.tab
})

const crumbs = computed(() => {
  const trail = [{ label: activeRagName.value ?? '', to: activeRagId.value ? `/ai-apps/${activeRagId.value}` : undefined }]
  if (activeTabName.value) trail.push({ label: activeTabName.value })
  return trail
})
</script>
