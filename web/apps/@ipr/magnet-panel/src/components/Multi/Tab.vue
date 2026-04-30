<template>
  <div
    class="bg-light full-height stack"
    data-gap="0"
  >
    <km-tabs
      dense
      outside-arrows
      :align="$theme === &quot;default&quot; ? &quot;center&quot; : &quot;justify&quot;"
      no-caps
      :model-value="currentTab"
      breakpoint="450"
      @update:model-value="setActiveTab($event)"
    >
      <template
        v-for="(child, index) in panels"
        :key="index"
      >
        <km-tab
          class="bg-light"
          :name="child.name"
        >
          <template v-if="$theme === &quot;default&quot; || $theme === &quot;siebel&quot;">
            <div class="secondary-text km-title">
              {{ child.name }}
            </div>
          </template>
          <template v-else>
            <div class="km-tab-text">
              {{ child.name }}
            </div>
          </template>
        </km-tab>
      </template>
    </km-tabs>
    <template v-if="panels.length &gt; 0">
      <km-tab-panels
        v-model="currentTab"
        class="fit rounded-borders"
      >
        <template
          v-for="panel in panels"
          :key="panel.name"
        >
          <km-tab-panel
            class="p-0"
            :name="panel.name"
          >
            <component
              :is="panel.component.name"
              :key="panel.name"
              v-bind="panel.component.props"
            />
          </km-tab-panel>
        </template>
      </km-tab-panels>
    </template>
    <template v-else>
      <div class="bg-light pt-xl justify-center flex text-secondary-text km-title">
        {{ m.panel_noAvailableTabsMulti() }}
      </div>
    </template>
  </div>
</template>

<script>
import { defineComponent, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useAiApps } from '@/pinia'
import getTabComponent from '@shared/utils/getTabComponent'

export default defineComponent({
  props: ['children'],
  setup() {
    const currentTab = ref('')
    const aiAppsStore = useAiApps()
    return { currentTab, aiAppsStore, m }
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
