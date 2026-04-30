// import store from '@/store'
import { globalProperties } from '@shared'
import { ref } from 'vue'
import { loadTheme } from '@themes'
window.consoleDebug = console.debug

const DEFAULT_THEME = 'default'
const DEFAULT_COLOR_MODE = 'light'
const COLOR_MODE_STORAGE_KEY = 'ds:theme'
const COLOR_MODE_VALUES = new Set(['light', 'dark'])

export const mountLog = (...args) => {
  consoleDebug('%c[mount]', 'color: white; background: #234f1e; padding: 2px; border-radius: 3px;', ...args)
}

const getStoredColorMode = () => {
  if (typeof localStorage === 'undefined') return DEFAULT_COLOR_MODE
  const storedMode = localStorage.getItem(COLOR_MODE_STORAGE_KEY)
  return COLOR_MODE_VALUES.has(storedMode) ? storedMode : DEFAULT_COLOR_MODE
}

const resolveThemeRequest = (requestedTheme) => {
  const requested = typeof requestedTheme === 'string' && requestedTheme ? requestedTheme : DEFAULT_THEME
  if (COLOR_MODE_VALUES.has(requested)) {
    return { themeName: DEFAULT_THEME, colorMode: requested, hasExplicitColorMode: true }
  }

  const [themeName = DEFAULT_THEME, colorMode] = requested.split(':')
  const hasExplicitColorMode = COLOR_MODE_VALUES.has(colorMode)
  return {
    themeName: themeName || DEFAULT_THEME,
    colorMode: hasExplicitColorMode ? colorMode : getStoredColorMode(),
    hasExplicitColorMode,
  }
}

const applyThemeAttributes = ({ app, rootId, themeName, colorMode }) => {
  app.config.globalProperties.$theme = themeName
  app.config.globalProperties.$themeMode = colorMode

  document.documentElement.setAttribute('data-theme', colorMode)
  document.documentElement.setAttribute('data-app-theme', themeName)
  document.documentElement.style.colorScheme = colorMode

  document.body.setAttribute('data-theme', themeName)
  document.body.setAttribute('data-color-mode', colorMode)

  const root = document.getElementById(rootId)
  if (root) {
    root.setAttribute('data-theme', themeName)
    root.setAttribute('data-color-mode', colorMode)
  }
}

export const setTheme = (newTheme, theme, panel, router, app, rootId) => {
  const { themeName, colorMode, hasExplicitColorMode } = resolveThemeRequest(newTheme)
  mountLog('Setting theme:', { requested: newTheme, themeName, colorMode })
  if (hasExplicitColorMode) {
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, colorMode)
  }
  if (newTheme != theme && panel) {
    localStorage.setItem(`km_panel_theme`, newTheme)
    router.go(0)
  } else {
    applyThemeAttributes({ app, rootId, themeName, colorMode })
    loadTheme(themeName)
  }
}

export const registerComponents = (app, componentList) => {
  mountLog('Register components')
  componentList.forEach((item) => {
    app.component(item.componentName, item.componentConfig.default || item.componentConfig)
  })
  consoleDebug(app?._context?.components)
}

export const registerGlobalProperties = (app) => {
  mountLog('Register global properties')
  app.config.globalProperties.$theme = ref('default') // Set default theme
  app.config.globalProperties.$themeMode = ref('light')
  Object.entries(globalProperties).forEach(([key, value]) => {
    Object.defineProperty(app.config.globalProperties, key, value)
  })
}
export const errorHandler = (err) => {
  console.error(err)
  // Uncomment when store is available:
  // const errorMessage = {
  //   technicalError: err.toString(),
  // }
  // store.commit('set', { errorMessage, globalLoading: false, lockUI: false })
}

export const getAppHoverDirective = () => {
  return {
    beforeMount(el, binding, vnode) {
      // Create reusable handlers
      el._onMouseEnter = function () {
        if (binding.arg in vnode.context) {
          vnode.context[binding.arg] = true
        }
      }
      el._onMouseLeave = function () {
        if (binding.arg in vnode.context) {
          vnode.context[binding.arg] = false
        }
      }

      // Add event listeners
      el.addEventListener('mouseenter', el._onMouseEnter)
      el.addEventListener('mouseleave', el._onMouseLeave)
    },
    beforeUnmount(el) {
      // Remove event listeners
      el.removeEventListener('mouseenter', el._onMouseEnter)
      el.removeEventListener('mouseleave', el._onMouseLeave)

      // Clean up references
      delete el._onMouseEnter
      delete el._onMouseLeave
    },
  }
}

export const registerDirectives = (app) => {
  mountLog('Register app directives')
  app.directive('hover', getAppHoverDirective())
}
