<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(style='max-width: 1200px; margin: 0 auto')
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md.q-mt-lg
          q-tabs(
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
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            template(v-if='tab == "ModelProviders"')
              model-providers-table
            template(v-if='tab == "DefaultModels"')
              model-providers-default-models
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
  
const route = useRoute()
const tab = ref('ModelProviders')
const tabs = ref([
  { name: 'ModelProviders', label: 'Model Providers' },
  { name: 'DefaultModels', label: 'Default Models' },
])

onMounted(() => {
  // Check if there's a tab query parameter
  if (route.query.tab) {
    tab.value = route.query.tab
  }
})

// Watch for route query changes
watch(() => route.query.tab, (newTab) => {
  if (newTab) {
    tab.value = newTab
  }
})



</script>