<template lang="pug">
layouts-details-layout(:contentContainerStyle='{ maxWidth: "1200px", margin: "0 auto" }')
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
    .full-width
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
        model-providers-models(v-if='tab == "models"')
        model-providers-settings(v-if='tab == "settings"')
  template(#drawer)
    model-providers-model-drawer(v-if='tab == "models" && validSelectedModel')
    model-providers-drawer(v-else-if='tab == "models" && availableModels.length > 0 && !validSelectedModel')
</template>

<script>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'
import { beforeRouteEnter } from '@/guards'

export default {
  beforeRouteEnter,
  setup() {
    const { selectedRow, ...useCollection } = useChroma('provider')
    const { visibleRows: allModels } = useChroma('model')

    return {
      tab: ref('models'),
      tabs: ref([
        { name: 'models', label: 'Models' },
        { name: 'settings', label: 'Settings' },
      ]),
      showInfo: ref(false),
      selectedRow,
      useCollection,
      allModels,
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    selectedModel() {
      return this.$store.getters['modelConfig/entity']
    },
    availableModels() {
      if (!this.provider?.system_name) {
        return []
      }
      return this.allModels.filter((item) => item.provider_system_name === this.provider.system_name)
    },
    validSelectedModel() {
      // Check if selectedModel exists in availableModels for current provider
      if (!this.selectedModel || !this.availableModels.length) {
        return null
      }
      return this.availableModels.find((model) => model.id === this.selectedModel.id) || null
    },
    name: {
      get() {
        return this.provider?.name || ''
      },
      set(value) {
        this.$store.commit('updateProviderProperty', { key: 'name', value })
      },
    },
    system_name: {
      get() {
        return this.provider?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateProviderProperty', { key: 'system_name', value })
      },
    },
  },
  watch: {
    selectedRow: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.$store.commit('setProvider', newVal)
        }
      },
    },
    availableModels: {
      immediate: true,
      handler(newVal, oldVal) {
        // Reset selectedModel if it's not in availableModels for current provider
        if (this.selectedModel && newVal.length > 0) {
          const modelExists = newVal.find((model) => model.id === this.selectedModel.id)
          if (!modelExists) {
            this.$store.commit('modelConfig/setEntity', null)
            // Auto-select first model if no valid selection
            this.autoSelectFirstModel(newVal)
          }
        } else if (this.selectedModel && newVal.length === 0) {
          // No models available for this provider, clear selection
          this.$store.commit('modelConfig/setEntity', null)
        } else if (!this.selectedModel && newVal.length > 0) {
          // No model selected but models are available, auto-select first
          this.autoSelectFirstModel(newVal)
        }
      },
    },
  },
  mounted() {
    // Auto-selection will be handled by availableModels watcher
    // No need to select here as availableModels might not be loaded yet
  },
  methods: {
    autoSelectFirstModel(models) {
      // Sort by is_default (descending) to prioritize default models
      const sortedModels = [...models].sort((a, b) => {
        if (a.is_default && !b.is_default) return -1
        if (!a.is_default && b.is_default) return 1
        return 0
      })

      if (sortedModels.length > 0) {
        this.$store.commit('modelConfig/setEntity', sortedModels[0])
      }
    },
  },
}
</script>
