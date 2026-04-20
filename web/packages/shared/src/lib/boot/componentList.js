import upperFirst from 'lodash/upperFirst'
import camelCase from 'lodash/camelCase'
import { defineAsyncComponent } from 'vue'

/**
 * Build a `[{ componentName, componentConfig }]` list from an
 * `import.meta.glob('components/**')` result.
 *
 * Accepts both glob modes:
 *   • eager: true  — `definition` is the module (`{ default: Component }`).
 *   • eager: false — `definition` is a factory (`() => Promise<Module>`).
 *
 * For lazy factories we wrap with `defineAsyncComponent`, which makes Vue
 * fetch the chunk the first time the component is rendered. Combined with
 * Vite's Rollup code-splitting this turns the previous ~400-file eager
 * bundle into per-component async chunks — see §C.5 in
 * docs/FRONTEND_FIXES_ROADMAP.md.
 */
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

      const componentConfig = typeof definition === 'function'
        // Lazy factory from `import.meta.glob(..., { eager: false })`.
        // `delay: 200` skips the loading component for fast (cached) loads
        // so the UX only changes for genuinely slow ones.
        ? defineAsyncComponent({
            loader: definition,
            delay: 200,
            timeout: 15_000,
          })
        // Eager module from `{ eager: true }`.
        : definition?.default ?? definition

      list.push({ componentName, componentConfig, fileName: relativePath })
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
