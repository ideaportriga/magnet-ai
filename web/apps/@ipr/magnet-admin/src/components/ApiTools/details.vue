<template lang="pug">
layouts-details-layout(
  :variants='variants',
  :selected-variant='selectedVariant',
  :active-variant='activeVariant',
  @activate-variant='store.commit("activateApiToolVariant")',
  @add-variant='store.commit("createApiToolVariant")',
  @delete-variant='store.commit("deleteApiToolVariant")',
  @select-variant='store.commit("setSelectedApiToolVariant", $event)',
  @update-variant-property='store.commit("updateNestedApiToolProperty", $event)'
)
  template(#header)
    layouts-details-header(v-model:name='name', v-model:description='description', v-model:systemName='system_name', :infoText='infoText')
    q-separator.q-mt-8
    .row.items-end.q-pt-8.q-gap-4
      .km-input-label.q-pl-6.text-secondary-text.q-pb-4(style='line-height: 16px') API Provider
      km-select-flat(placeholder='API Provider', :options='apiProviderOptions', v-model='apiProvider')

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
      api-tools-tabs-information(v-if='tab == "information"', :apiTool='apiTool')
      api-tools-tabs-parameters(v-if='tab == "parameters"', :apiTool='apiTool', @select='selectedRow = $event', :selectedRow='selectedRow')

  template(#drawer)
    api-tools-drawer(v-model:open='openPropDetails', :selectedRow='selectedRow', ref='drawer')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { useStore } from 'vuex'
import _ from 'lodash'
export default {
  setup() {
    const { items } = useChroma('api_tools')
    const { items: apiProviders } = useChroma('api_tool_providers')
    const store = useStore()

    return {
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'information', label: 'API Information' },
      ]),
      items,
      apiProviders,
      openPropDetails: ref(false),
      selectedRow: ref(null),
      store,
    }
  },
  computed: {
    apiTool() {
      return this.items.find((item) => item.id === this.$route.params.id) ?? {}
    },
    apiProvider: {
      get() {
        const apiProvider = this.$store.getters.api_tool?.api_provider || ''
        return {
          label: apiProvider,
          value: apiProvider,
        }
      },
      set({ value }) {
        this.$store.commit('updateApiToolProperty', { key: 'api_provider', value })
      },
    },
    apiProviderOptions() {
      return this.apiProviders.map((apiProvider) => ({
        label: apiProvider.systemName,
        value: apiProvider.systemName,
      }))
    },
    name: {
      get() {
        return this.$store.getters.api_tool?.name || ''
      },
      set(value) {
        this.$store.commit('updateApiToolProperty', { key: 'name', value })
      },
    },
    description: {
      get() {
        return this.$store.getters.api_tool?.description || ''
      },
      set(value) {
        this.$store.commit('updateApiToolProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.$store.getters.api_tool?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateApiToolProperty', { key: 'system_name', value })
      },
    },
    variant: {
      get() {
        return this.$store.getters.api_tool_variant
      },
    },
    variants() {
      return this.$store.getters.api_tool?.variants
    },
    selectedVariant: {
      get() {
        return this.$store.getters.selectedApiToolVariant
      },
      set(value) {
        this.$store.commit('setSelectedApiToolVariant', value.value)
      },
    },
    activeVariant: {
      get() {
        return this.$store.getters.api_tool?.active_variant
      },
    },
  },
  watch: {
    apiTool: {
      handler(newVal) {
        this.$store.commit('setApiTool', _.cloneDeep(newVal))
      },
      deep: true,
    },
    selectedRow: {
      handler() {
        this.$refs.drawer.setTab('details')
      },
      deep: true,
    },
    tab: {
      handler(newVal) {
        this.$refs.drawer?.regulateTabs(newVal)
      },
      immediate: true,
    },
  },
  mounted() {
    this.$store.commit('setApiTool', _.cloneDeep(this.apiTool))
  },
}
</script>
