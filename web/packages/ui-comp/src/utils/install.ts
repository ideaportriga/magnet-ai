import { App } from 'vue'
import { getComponentList } from './componentList'

const components = import.meta.glob('../components/**/*.vue', { eager: true })
const componentList = getComponentList(components)

export const registerComponents = (app, componentList) => {
  componentList.forEach((item) => {
    app.component(item.componentName, item.componentConfig.default || item.componentConfig)
  })
}

export default {
  install(app: App) {
    registerComponents(app, componentList)
  },
}
