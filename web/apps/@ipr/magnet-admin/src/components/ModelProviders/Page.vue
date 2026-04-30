<template>
  <km-list-page>
    <template #tabs>
      <km-tabs v-model="tab" class="bb-border full-width mb-lg" align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
    </template>
    <template v-if="tab == 'ModelProviders'">
      <model-providers-table />
    </template>
    <template v-if="tab == 'DefaultModels'">
      <model-providers-default-models />
    </template>
  </km-list-page>
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'

const route = useRoute()
const tab = ref('ModelProviders')
const tabs = ref([
  { name: 'ModelProviders', label: 'Model Providers' },
  { name: 'DefaultModels', label: 'Default Models' },
])

onMounted(() => {
  if (route.query.tab) {
    tab.value = route.query.tab
  }
})

watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab) {
      tab.value = newTab
    }
  }
)
</script>
