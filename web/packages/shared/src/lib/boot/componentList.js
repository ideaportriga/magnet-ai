import upperFirst from 'lodash/upperFirst'
import camelCase from 'lodash/camelCase'

export function getComponentList(components) {
  // Automatic Global Registration of Components
  const baseComponentPrefix = 'km'
  const matchFile = /[\w-]+\.vue$/
  const list = []

  Object.entries(components).forEach(([path, definition]) => {
    let relativePath = getRelativePath(path)
    const fileName = path
      .split('/')
      .pop()
      .replace(/\.\w+$/, '')

    if (relativePath.match(matchFile)) {
      if (fileName === 'index') {
        relativePath = relativePath.slice(0, -fileName.length - 5)
      }
      const componentName = relativePath.startsWith('base')
        ? upperFirst(
            camelCase(
              relativePath
                .split('/')
                .slice(1)
                .join('/')
                .replace(/^(.*)\.\w+$/, `${baseComponentPrefix}$1`)
            )
          )
        : relativePath.startsWith('shared')
          ? upperFirst(
              camelCase(
                relativePath
                  .split('/')
                  .slice(2)
                  .join('/')
                  .replace(/^(.*)\.\w+$/, `$1`)
              )
            )
          : upperFirst(camelCase(relativePath.replace(/^(.*)\.\w+$/, '$1'))) // by folder and file name=

      list.push({ componentName, componentConfig: definition.default, fileName: relativePath })
    }
  })
  return list
}

const getRelativePath = (fullPath) => {
  const segments = fullPath.split('/')

  // Check if the path contains enough segments
  const startIndex = segments.indexOf('components')

  if (startIndex !== -1) {
    return segments.slice(startIndex + 1).join('/')
  }
  return ''
}
