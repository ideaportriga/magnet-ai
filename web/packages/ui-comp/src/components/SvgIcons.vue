<template lang="pug">
svg(width='0', height='0', v-html='svgsContent')
</template>

<script>
import { ref, onMounted, computed, getCurrentInstance } from 'vue'

export default {
  setup() {
    const components = ref({})
    const { appContext } = getCurrentInstance()
    const theme = appContext.config.globalProperties.$theme
    onMounted(() => {
      const baseIcons = import.meta.glob('@/assets/svg/*.svg', { query: '?raw', import: 'default', eager: true })
      let themeIcons = {}
      if (theme === 'siebel') themeIcons = import.meta.glob('@/assets/svg/redwood/*.svg', { query: '?raw', import: 'default', eager: true })
      if (theme === 'salesforce') themeIcons = import.meta.glob('@/assets/svg/salesforce/*.svg', { query: '?raw', import: 'default', eager: true })
      themeIcons = {
        ...themeIcons,
        ...import.meta.glob('@/assets/svg/theme/*.svg', { query: '?raw', import: 'default', eager: true }),
      }
      const componentFiles = { ...baseIcons, ...themeIcons }
      for (const path in componentFiles) {
        const componentName = path.split('/').pop().split('.').shift()
        // Add a unique id to each component based on its name
        const componentId = `icon-${componentName.toLowerCase()}`
        const svgContent = componentFiles[path]
        components.value[componentName] = svgContent.replace('<svg', `<svg id="${componentId}"`)
      }
    })
    const svgsContent = computed(() => Object.values(components.value).join(''))
    return {
      components,
      svgsContent,
    }
  },
}
</script>
