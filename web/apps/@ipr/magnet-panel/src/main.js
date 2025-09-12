import '../public-path.js'
window.appPublicPath = window.SiebelApp?.S_App ? window.kmPanelPublicPath : ''
// Import Vue core modules
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { quasarConf } from '@shared'
import { Quasar } from 'quasar'
import 'quasar/src/css/index.sass'

// Import utility functions and helpers
import { setTheme, registerComponents, registerGlobalProperties, errorHandler, registerDirectives, mountLog } from '@shared/utils/mountUtils'
import { getComponentList } from '@shared'

import uiComps from '@ui'

import App from './App.vue'

import { useMainStore } from '@/pinia'

// Set default theme
const theme = localStorage.getItem('km_panel_theme') ?? 'siebel'
// Import and merge all components
const components = import.meta.glob('@/components/**', { eager: true })

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
