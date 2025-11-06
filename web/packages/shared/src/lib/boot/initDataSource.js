export default async ({ store }) => {
  consoleDebug('run dataSource.js')

  const views = store.getters.views

  // RUNNING FROM SIEBEL
  if (window.SiebelApp?.S_App && window.dataSourceManualValue !== 'mock') {
    consoleDebug('run dataSource.js in siebelAppFacade')

    const viewName = store.getters.getViewName()
    store.commit('set', { viewName })
    const entities = views?.[viewName]?.entities ?? []
    const viewAppletList = Object.keys(window.SiebelApp.S_App.GetActiveView().GetAppletMap())

    // connect nexus  store
    if (!nexusStore.registered) {
      store.registerModule('nexus', nexusStore)
      consoleDebug('registering store nexus module', store)
      nexusStore.registered = true
    }

    const n19setup = {}
    Object.entries(entities).forEach(([entity, appletName]) => {
      if (!viewAppletList.includes(appletName)) console.warn(`[DATA SOURCE]: Applet [${appletName}] is missing on the view, entity ${entity}`)
      else n19setup[entity] = initializeNexus(appletName)
    })

    store.commit('set', {
      n19: n19setup,
    })

    Object.keys(entities).forEach((entity) => store.dispatch('init', entity))
  }
}
