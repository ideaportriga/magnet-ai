<template lang="pug">
.bg-panel-main-bg.full-height.column.no-wrap.bl-border.relative-position(v-if='panels.length > 0')
  .flex.row.justify-between.items-center.bg-header-bg.q-px-md(style='height: 55px')
    //logo
    .flex.items-center.justify-center(:style='{ width: "32px", height: "32px", borderRadius: "50%" }', :class='{ "bg-white": !isIconHide }')
      km-icon(:name='"magnet"', width='21', height='23', v-if='!isIconHide')
    //dropdown

    .col-auto.header-select(:style='{ minWidth: $theme === "salesforce" ? "150px" : "240px" }')
      km-select(height='30px', :options='panels', option-value='value', v-model='tab', @update:model-value='changePanel')
    //close button
    .flex.items-center.justify-center(:style='{ width: "32px", height: "32px", borderRadius: "50%" }')
      q-item(clickable, dense, v-if='show_close_button')
        q-icon.q-pa-xs.rounded-borders(name='close', rounded, size='20px', color='white', @click='hidePanel')
  km-image.redwood-strip(src='strip.png', v-if='$theme === "siebel"')
  q-tab-panels.fit.rounded-borders(v-model='tab')
    template(v-for='(panel, index) in panels')
      q-tab-panel.q-pa-none(:name='panel.name')
        component(:is='panel.component.name', :key='`${ai_app?.system_name} ${panel.name}`', v-bind='panel.component.props', :index='index')

//loading
.bg-light.fit.column.no-wrap.q-pt-xs.bl-border.bg-light.items-center.justify-center(v-else-if='ai_app === undefined')
  q-spinner.text-primary(size='80px')
.bg-light.fit.column.no-wrap.q-pt-xs.bl-border.bg-light.items-center.justify-center(v-else-if='ai_app === null')
  empty-tab(text='There are no available app for this system name')
.bg-light.fit.column.no-wrap.q-pt-xs.bl-border.bg-light.items-center.justify-center(v-else)
  empty-tab

//footer
.bg-footer-bg.full-width.row.justify-center.items-center.footer.items-center
  .footer-text Powered by Magnet AI by IdeaPort Riga
</template>

<script>
import { ref, getCurrentInstance } from 'vue'
import getTabComponent from '@shared/utils/getTabComponent'
import { useMainStore, useAiApps } from '@/pinia'
export default {
  setup() {
    const mainStore = useMainStore()
    const aiAppsStore = useAiApps()

    const tab = ref('')
    const { appContext } = getCurrentInstance()
    const isIframe = appContext.config.globalProperties.$iframe
    const parentApp = ref(null)
    return { tab, isIframe, parentApp, appContext, mainStore, aiAppsStore }
  },
  computed: {
    loading() {
      return this.mainStore.globalLoading
    },
    baseUrl() {
      return {
        admin: this.mainStore.config?.admin?.baseUrl,
        panel: this.mainStore.config?.panel?.baseUrl,
      }
    },
    ai_app() {
      //TODO CHANGE TO ACTUAL PARENT TABS
      if (this.isIframe)
        return {
          ...this.parentApp,
          tabs: this.aiAppsStore?.app?.tabs || [],
        }
      return this.aiAppsStore.app
    },
    panels() {
      if (!this.ai_app) return []
      if (!this.ai_app.tabs?.length > 0) return []
      return this.ai_app.tabs
        .filter((item) => !item.inactive)
        .map((item, index) => ({
          name: item.name,
          label: item.name,
          component: getTabComponent(item),
          disable: false,
          index: index,
        }))
    },
    isIconHide() {
      return this.ai_app?.settings?.is_icon_hide
    },
    show_close_button() {
      return this.ai_app?.settings?.show_close_button || false
    },
    appTheme() {
      if (!this.ai_app) return
      return this.ai_app.settings.theme ?? 'siebel'
    },
  },
  watch: {
    loading: {
      immediate: true,
      handler(val) {
        if (val) {
          this.$q.loading.show()
        } else {
          this.$q.loading.hide()
        }
      },
    },
    panels: {
      immediate: true,
      handler(val) {
        this.tab = (val || [])?.[0]?.name
      },
    },
    appTheme: {
      immediate: true,
      handler(val) {
        if (val) {
          this.appContext.config.globalProperties.$setTheme(val)
        }
      },
    },
  },
  mounted() {
    if (this.isIframe) {
      window.addEventListener(
        'message',
        (event) => {
          debugger;
          console.log('event', event)
          if (event.origin !== this.baseUrl?.admin) return
          this.parentApp = JSON.parse(event.data.app) // JSON.parse(event.data.app)
        },
        true
      )
      if (this.baseUrl?.admin) window.parent.postMessage({ type: 'reload_app' }, this.baseUrl?.admin)
    }

    this.tab = (this.ai_app?.tabs || []).filter((item) => !item?.inactive)?.[0]?.name
  },
  methods: {
    changePanel(value) {
      // if (value !== 'more') {
      //   this.showMoreDropdown = false
      //   this.tab = value
      // } else {
      //   this.showMoreDropdown = !this.showMoreDropdown
      // }
      this.tab = value.name
      this.aiAppsStore.setSelectedTab(this.ai_app.tabs[value.index])
    },

    hidePanel() {
      document.getElementById('close-pane')?.click()
    },
  },
}
</script>

<style lang="scss" scoped>
.tabs-style {
  margin: 0 40px 0 60px;
}

.tabs-style-without-icon {
  margin: 0 40px 0 4px;
}
</style>
