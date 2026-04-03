import '../public-path.js'

// Import Vue core modules
import { createApp } from 'vue'

// Import shared styles and configurations
import { loadTheme } from '@themes'
import 'animate.css/animate.min.css'
import 'quasar/src/css/index.sass'
import '@/assets/layout.css'
import { quasarConf } from '@shared'
import { Quasar } from 'quasar'

// Import utility functions and helpers
import { setTheme, registerComponents, registerGlobalProperties, errorHandler, registerDirectives, mountLog } from '@shared/utils/mountUtils'

import { getComponentList } from '@shared'
import uiComps from '@ui'

// Import app core files
import App from './App.vue'
import router from '@/router'

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

    // Initialize Pinia + TanStack Query BEFORE router (router guards use Pinia stores)
    const { initNewStack } = await import('@/plugins/initNewStack')
    await initNewStack(appInstance)

    // Provide Pinia stores and data for ui-comp components that need them
    const { useAppStore } = await import('@/stores/appStore')
    appInstance.provide('appStore', useAppStore())

    // Install plugins (router must come AFTER Pinia)
    appInstance.use(router)
    appInstance.use(Quasar, quasarConf)
    appInstance.use(uiComps)

    // Register components, properties and directives
    registerComponents(appInstance, componentList)
    registerGlobalProperties(appInstance)
    registerDirectives(appInstance)

    // Configure app instance
    appInstance.config.errorHandler = (err, instance, info) => {
      console.error(err)
      try {
        const appStore = useAppStore()
        appStore.setErrorMessage({
          text: 'An unexpected error occurred',
          technicalError: err instanceof Error ? err.message : String(err),
          stack: err instanceof Error ? err.stack : undefined,
        })
      } catch {
        // appStore not ready — fall back to default handler
        errorHandler(err, instance, info)
      }
    }
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
    return null
  },
  get router() {
    return router
  },
}

// Ship console.error / console.warn / unhandledrejection to local Loki
import { initLokiLogger } from '@/plugins/lokiLogger'
initLokiLogger()

// Initialize and run the app
;(async () => {
  await app.init()
  app.run({})
})()
