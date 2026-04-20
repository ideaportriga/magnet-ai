import '../public-path.js'
window.appPublicPath = window.SiebelApp?.S_App ? window.kmPanelPublicPath : ''
// Import Vue core modules
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { quasarConf } from '@shared'
import { Quasar } from 'quasar'
import 'quasar/src/css/index.sass'

// Import i18n (Paraglide JS)
import * as runtime from '@/paraglide/runtime'
import { initLocale } from '@shared/i18n'
initLocale(runtime)

// Import utility functions and helpers
import { setTheme, registerComponents, registerGlobalProperties, errorHandler, registerDirectives, mountLog } from '@shared/utils/mountUtils'
import { getComponentList } from '@shared'

// eslint-disable-next-line @nx/enforce-module-boundaries
import uiComps from '@ui'

import App from './App.vue'

import { useMainStore } from '@/pinia'

// Set default theme
const theme = localStorage.getItem('km_panel_theme') ?? 'siebel'
// §C.5 — see magnet-admin/src/main.js. Lazy glob + defineAsyncComponent
// so app components are split into per-chunk async modules.
const components = import.meta.glob('@/components/**/*.vue')

const componentList = getComponentList(components)

let appInstance = {},
  store = {},
  router = {}

const app = {
  init: async () => {
    //store = (await import('@/store/index')).default
    router = (await import('@/router')).default
  },

  run: async ({ appId = 'km-app' }) => {
    mountLog('Running app', { appId })
    appInstance = createApp(App)

    const urlParams = new URLSearchParams(window.location.hash)
    const iframeParam = urlParams.get('iframe')

    // Install plugins
    //appInstance.use(store)
    appInstance.use(createPinia())
    store = useMainStore()
    appInstance.use(router)

    // Initialize TanStack Query + shared entity queries
    const { installVueQuery } = await import('@/plugins/vueQuery')
    installVueQuery(appInstance)

    // Load config first, then init entity APIs
    await store.loadConfig()

    if (store.endpoint?.admin) {
      const { createPanelEntityApis } = await import('@/api/entityApis')
      const { initPanelEntityQueries } = await import('@/queries/entities')
      const apis = createPanelEntityApis(store.endpoint.admin, store.config?.credentials ?? 'include')
      initPanelEntityQueries(apis)
    }
    appInstance.use(Quasar, quasarConf)
    appInstance.use(uiComps)

    // Register components, properties and directives
    registerComponents(appInstance, componentList)
    registerGlobalProperties(appInstance)
    registerDirectives(appInstance)

    // Configure app instance
    appInstance.config.globalProperties.$appPublicPath = window.SiebelApp?.S_App ? window.kmPanelPublicPath : ''
    appInstance.config.globalProperties.$appImagePath = appInstance.config.globalProperties.$appPublicPath + '/images/'
    appInstance.config.errorHandler = (error) => {
      useMainStore().setErrorMessage({
        technicalError: error.toString(),
      })
      console.error(error)
    }
    appInstance.config.globalProperties.$setTheme = (newTheme) => setTheme(newTheme, theme, false, router, appInstance, appId)
    appInstance.config.globalProperties.$iframe = iframeParam

    // Set initial theme
    appInstance.config.globalProperties.$setTheme(theme)

    // Initialize store and data
    window.store = store
    appInstance.mount(`#${appId}`)
  },

  close: async () => {
    useMainStore().appVisible = false
    consoleDebug('CLOSE APP')
  },
}

window.panelApp = {
  ...app,
  get appInstance() {
    return appInstance
  },
  set appInstance(newAppInstance) {
    appInstance = newAppInstance
  },
  get store() {
    return store
  },
  get router() {
    return router
  },
}

// Initialize the app if it is not in Siebel
;(async () => {
  await app.init()
  app.run({})
})()
