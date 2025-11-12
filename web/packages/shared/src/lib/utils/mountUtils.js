// import store from '@/store'
import { globalProperties } from '@shared'
import { ref } from 'vue'
import { loadTheme } from '@themes'
window.consoleDebug = console.debug

export const mountLog = (...args) => {
  consoleDebug('%c[mount]', 'color: white; background: #234f1e; padding: 2px; border-radius: 3px;', ...args)
}

export const setTheme = (newTheme, theme, panel, router, app, rootId) => {
  mountLog('Setting theme:', newTheme)
  if (newTheme != theme && panel) {
    localStorage.setItem(`km_panel_theme`, newTheme)
    router.go(0)
  } else {
    app.config.globalProperties.$theme = newTheme // Update the current theme
    document.body.setAttribute('data-theme', newTheme)
    document.querySelector(`#${rootId}`).setAttribute('data-theme', newTheme)
    loadTheme(newTheme)
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
