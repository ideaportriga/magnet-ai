export default (theme) => {
  const components = {}
  const baseIcons = import.meta.glob('../base/assets/svg/*.svg', {
    query: '?raw',
    import: 'default',
    eager: true,
  })
  console.log('baseIcons', baseIcons)
  let themeIcons = {}
  if (theme === 'siebel')
    themeIcons = import.meta.glob('../themes/siebel/svg/*.svg', {
      query: '?raw',
      import: 'default',
      eager: true,
    })
  if (theme === 'salesforce')
    themeIcons = import.meta.glob('../themes/salesforce/svg/*.svg', {
      query: '?raw',
      import: 'default',
      eager: true,
    })
  const componentFiles = { ...baseIcons, ...themeIcons }
  for (const path in componentFiles) {
    const componentName = path.split('/').pop().split('.').shift()
    const svgContent = componentFiles[path]
    const componentId = `icon-${componentName.toLowerCase()}`
    components[componentName] = svgContent.replace('<svg', `<svg id="${componentId}"`)
  }

  const existingSvgMap = document.getElementById('svg-map')
  if (existingSvgMap) {
    existingSvgMap.parentNode.removeChild(existingSvgMap)
  }
  const el = document.createElement('svg')
  el.setAttribute('id', 'svg-map')
  el.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  el.setAttribute('style', 'position: absolute; width: 0; height: 0; overflow: hidden;')
  el.innerHTML = `<defs>${Object.values(components).join('')}</defs>`
  document.body.appendChild(el)
}
