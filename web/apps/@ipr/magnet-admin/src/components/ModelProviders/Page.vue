<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    q-tabs.bb-border.full-width.q-mb-lg(
      v-model='tab',
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      template(v-if='tab == "ModelProviders"')
        model-providers-table
      template(v-if='tab == "DefaultModels"')
        model-providers-default-models
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
