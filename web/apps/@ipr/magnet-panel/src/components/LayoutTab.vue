<template>
  <div
    v-if="panels.length &gt; 0"
    class="stack bg-panel-main-bg full-height bl-border relative-position"
    data-gap="0"
    data-test="panel-layout"
  >
    <div
      class="cluster bg-header-bg px-md"
      data-wrap="no"
      data-justify="between"
      style="block-size: 55px"
      data-test="panel-header"
    >
      <!--logo-->
      <div
        class="flex items-center justify-center"
        :style="{ width: &quot;32px&quot;, height: &quot;32px&quot;, borderRadius: &quot;50%&quot; }"
        :class="{ &quot;bg-white&quot;: !isIconHide }"
      >
        <km-icon
          v-if="!isIconHide"
          :name="&quot;magnet&quot;"
          width="21"
          height="23"
        />
      </div>
      <!--dropdown-->
      <div
        class="flex-none header-select"
        :style="{ minWidth: $theme === &quot;salesforce&quot; ? &quot;150px&quot; : &quot;240px&quot; }"
      >
        <km-select
          v-model="tab"
          height="30px"
          :options="panels"
          option-value="value"
          @update:model-value="changePanel"
        />
      </div>
      <!--close button and user menu-->
      <div
        class="cluster"
        data-wrap="no"
      >
        <user-menu
          v-if="auth.authenticated"
          class="mr-sm"
          :user-info="auth.userInfo"
          @logout="handleLogout"
          @navigate="handleNavigate"
        />
      </div>
      <div
        class="flex items-center justify-center"
        :style="{ width: &quot;32px&quot;, height: &quot;32px&quot;, borderRadius: &quot;50%&quot; }"
      >
        <button
          v-if="show_close_button"
          class="flex items-center justify-center p-0 bg-transparent border-0 cursor-pointer"
          type="button"
          data-test="panel-close"
          @click="hidePanel"
        >
          <km-glyph
            class="p-xs rounded-borders"
            name="close"
            rounded
            size="20px"
            tone="inverse"
          />
        </button>
      </div>
    </div>
    <km-image
      v-if="$theme === &quot;siebel&quot;"
      class="redwood-strip"
      src="strip.png"
    />
    <km-tab-panels
      v-model="tab"
      class="fit rounded-borders"
    >
      <template
        v-for="(panel, index) in panels"
        :key="index"
      >
        <km-tab-panel
          class="p-0"
          :name="panel.name"
        >
          <component
            :is="panel.component.name"
            :key="`${ai_app?.system_name} ${panel.name}`"
            v-bind="panel.component.props"
            :index="index"
          />
        </km-tab-panel>
      </template>
    </km-tab-panels>
  </div>
  <!--loading-->
  <div
    v-else-if="ai_app === undefined"
    class="flex items-center justify-center bg-light fit bl-border pt-xs"
    data-test="panel-loading"
  >
    <km-loader
      class="text-primary"
      size="80px"
    />
  </div>
  <div
    v-else-if="ai_app === null"
    class="flex items-center justify-center bg-light fit bl-border pt-xs"
    data-test="panel-empty-no-app"
  >
    <empty-tab :text="m.panel_noAvailableApp()" />
  </div>
  <div
    v-else
    class="flex items-center justify-center bg-light fit bl-border pt-xs"
    data-test="panel-empty"
  >
    <empty-tab />
  </div>
  <!--footer-->
  <div
    class="cluster bg-footer-bg full-width footer"
    data-justify="center"
    data-test="panel-footer"
  >
    <div class="footer-text">
      {{ m.panel_poweredBy() }}
    </div>
  </div>
</template>

<script>
import { ref, getCurrentInstance, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import getTabComponent from '@shared/utils/getTabComponent'
import { useMainStore, useAiApps, useAuth } from '@/pinia'
import { m } from '@/paraglide/messages'

const UserMenu = defineAsyncComponent(() => import('@ui/components/user/UserMenu.vue'))
export default {
  components: { UserMenu },
  setup() {
    const mainStore = useMainStore()
    const aiAppsStore = useAiApps()
    const auth = useAuth()
    const router = useRouter()

    const tab = ref('')
    const { appContext } = getCurrentInstance()
    const isIframe = appContext.config.globalProperties.$iframe
    const parentApp = ref(null)

    async function handleLogout() {
      await auth.logout()
      router.push('/login')
    }

    function handleNavigate(path) {
      router.push(path)
    }

    return { tab, isIframe, parentApp, appContext, mainStore, aiAppsStore, auth, handleLogout, handleNavigate, m }
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
      return this.ai_app?.settings?.theme ?? 'siebel'
    },
  },
  watch: {
    // The global loading overlay is owned by App.vue's watcher on
    // mainStore.globalLoading — duplicating it here previously double-counted
    // the overlay's pending counter and held the spinner open after this
    // component unmounted (HMR / navigation).
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
          if (event.origin !== this.baseUrl?.admin) return
          this.parentApp = JSON.parse(event.data.app)
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
