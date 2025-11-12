<template lang="pug">
.bg-light.full-height.column.no-wrap
  q-tabs(
    dense,
    active-color='primary',
    active-bg-color='light',
    outside-arrows,
    :align='$theme === "default" ? "center" : "justify"',
    no-caps,
    :model-value='currentTab',
    indicator-color='transparent',
    breakpoint='450',
    @update:modelValue='setActiveTab($event)'
  )
    template(v-for='(child, index) in panels')
      q-tab.bg-light(:name='child.name')
        template(v-if='$theme === "default" || $theme === "siebel"')
          .secondary-text.km-title {{ child.name }}
        template(v-else)
          .km-tab-text {{ child.name }}
  template(v-if='panels.length > 0')
    q-tab-panels.fit.rounded-borders(v-model='currentTab')
      template(v-for='panel in panels')
        q-tab-panel.q-pa-none(:name='panel.name')
          component(:is='panel.component.name', :key='panel.name', v-bind='panel.component.props')
  template(v-else)
    .bg-light.q-pt-xl.justify-center.flex.text-secondary-text.km-title There are no available tabs
</template>

<script>
import { defineComponent, ref } from 'vue'
import { useAiApps } from '@/pinia'
import getTabComponent from '@shared/utils/getTabComponent'

export default defineComponent({
  props: ['children'],
  setup() {
    const currentTab = ref('')
    const aiAppsStore = useAiApps()
    return { currentTab, aiAppsStore }
  },
  computed: {
    panels() {
      return (this.children ?? []).map((item, index) => {
        return {
          name: item.name,
          label: item.name,
          component: getTabComponent(item),
          disable: false,
          index: index,
        }
      })
    },
    selectedPanel() {
      return this.panels.find((item) => item.name === this.currentTab)
    },
    // panelNames() {
    //   return this.panels.map((item) => item.system_name)
    // },
  },
  watch: {
    panels: {
      handler: function (val) {
        if (val.length > 0) {
          this.currentTab = val[0].name
          this.aiAppsStore.setSelectedChild(0)
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    setActiveTab(value) {
      this.currentTab = value
      this.aiAppsStore.setSelectedChild(value.index)
    },
  },
})
</script>
