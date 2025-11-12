<template lang="pug">
layouts-details-layout.q-mx-auto.collection-container(v-if='target_api_server')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
        km-input-flat.col.km-description.text-black.full-width(
          placeholder='Enter system name',
          v-model='system_name',
          @focus='showInfo = true',
          @blur='showInfo = false'
        )
      .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
  template(#content)
    q-tabs.bb-border.full-width(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.q-gap-16.overflow-auto.q-pt-lg.q-pb-lg
      api-servers-tabs-tools(v-if='tab == "tools"')
      api-servers-tabs-settings(v-if='tab == "settings"')
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useChroma } from '@shared'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'

const route = useRoute()
const store = useStore()

const showInfo = ref(false)
const tab = ref('tools')
const tabs = ref([
  { name: 'tools', label: 'Tools' },
  { name: 'settings', label: 'Settings' },
])

const { items: api_servers } = useChroma('api_servers')

const api_server = computed(() => {
  return api_servers.value.find((item) => item.id === route.params.id)
})

const target_api_server = computed(() => {
  return store.getters.api_server
})

const name = computed({
  get() {
    return target_api_server.value.name
  },
  set(value) {
    store.dispatch('updateApiServerProperty', { key: 'name', value })
  },
})
const system_name = computed({
  get() {
    return target_api_server.value.system_name
  },
  set(value) {
    store.dispatch('updateApiServerProperty', { key: 'system_name', value })
  },
})

watch(
  () => api_server.value,
  (newVal) => {
    console.log('server', newVal)
    if (!newVal) return
    store.dispatch('setApiServer', newVal)
  },
  { immediate: true, deep: true }
)
</script>

<style lang="stylus"></style>
