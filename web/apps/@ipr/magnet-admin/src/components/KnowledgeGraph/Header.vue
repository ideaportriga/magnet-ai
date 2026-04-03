<template>
  <div class="col-auto q-py-auto">
    <div class="km-heading-4">{{ graphName }}</div>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'

const route = useRoute()
const appStore = useAppStore()
const graphName = ref('')

const graphId = computed(() => route.params.id as string)

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
