import '../public-path.js'

// Import Vue core modules
import { createApp } from 'vue'

// Import shared styles and configurations
import { loadTheme } from '@themes'
import 'animate.css/animate.min.css'
import 'quasar/src/css/index.sass'
import { quasarConf } from '@shared'
import { Quasar } from 'quasar'


// Import utility functions and helpers
import { setTheme, registerComponents, registerGlobalProperties, errorHandler, registerDirectives, mountLog } from '@shared/utils/mountUtils'

import { getComponentList } from '@shared'
import uiComps from '@ui'

// Import app core files
import App from './App.vue'
import router from '@/router'
import store from '@/store/index'

// Get URL parameters to check if running in iframe
const urlParams = new URLSearchParams(window.location.hash)
const theme = urlParams.get('km_panel_theme') || 'default'

// Import and merge all components
const components = import.meta.glob('@/components/**', { eager: true })

const componentList = getComponentList(components)
let appInstance = {}

const app = {
  init: async () => {
    loadTheme('default')
  },

  run: async ({ appInstanceName = 'vueKm', appId = 'km-app' }) => {
    mountLog('Running app', { appInstanceName, appId })

    // Create Vue app instance
    appInstance = createApp(App)

    // Initialize store and data
    await store.dispatch('loadConfig')

    // Install plugins
    appInstance.use(store)
    appInstance.use(router)
    appInstance.use(Quasar, quasarConf)
    appInstance.use(uiComps)

    // Register components, properties and directives
    registerComponents(appInstance, componentList)
    registerGlobalProperties(appInstance)
    registerDirectives(appInstance)

    // Configure app instance
    appInstance.config.errorHandler = errorHandler
    appInstance.config.globalProperties.$setTheme = (newTheme) => setTheme(newTheme, theme, false, router, appInstance, appId)
    appInstance.config.globalProperties.$appPublicPath = window.SiebelApp?.S_App ? window.kmPanelPublicPath : ''
    appInstance.config.globalProperties.$appImagePath = appInstance.config.globalProperties.$appPublicPath + '/images/'

    // Set initial theme
    appInstance.config.globalProperties.$setTheme(theme)

    // Mount app if not already mounted
    if (!window[appInstanceName]) {
      window[appInstanceName] = appInstance
      appInstance.mount(`#${appId}`)
    }
  },

}

// Make app instance and core modules available globally for debugging
window.mainApp = {
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

// Initialize and run the app
;(async () => {
  await app.init()
  app.run({})
})()
