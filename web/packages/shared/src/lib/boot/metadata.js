export default async ({ store }) => {
  let entities = {}
  const views = store.getters.views
  Object.keys(views).forEach((viewName) => (entities = { ...entities, ...(views[viewName]?.entities ?? {}) }))

  const meta = {}
  // await Promise.all(
  //   Object.keys(entities).map(async (entity) => {
  //     const location = `${window.__vite_public_path__ ?? ''}metadata/${entity}.json`
  //     try {
  //       const response = await fetch(location)
  //       if (response.ok) {
  //         const responseJson = await response.json()
  //         meta[entity] = responseJson
  //       }
  //     } catch (err) {
  //       console.error(`load metadata for [${entity}] failed:`, err)
  //       meta[entity] = { items: [], controls: {} }
  //     }
  //   })
  // )

  // TODO: handle kostyl
  Object.defineProperty(store, '$meta', { value: meta, configurable: true })

  consoleDebug('metadata load', meta)
}
