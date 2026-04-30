<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const route = useRoute()
const appStore = useAppStore()
const graphName = ref('')

const graphId = computed(() => route.params.id as string)

const crumbs = computed(() => [{ label: graphName.value }])

const load = async () => {
  if (!graphId.value) return
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${graphId.value}`,
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      const data = await response.json()
      graphName.value = data?.name || ''
    }
  } catch (e) {
    // noop
  }
}

onMounted(load)

watch(graphId, () => {
  load()
})
</script>
