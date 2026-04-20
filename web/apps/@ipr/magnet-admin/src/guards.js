const mapRoutesChildrenParent = {

  EvaluationSetDetails: 'EvaluationSets',
  PromptTemplatesItem: 'PromptTemplates',
  AIAppDetail: 'AIApp',
  ConfigurationItems: 'Configuration',
  RetrievalItems: 'Retrieval',
  ModelItems: 'Model',
  CollectionDetail: 'Collections',
  AssistantItems: 'Assistant',
}

const beforeRouteEnter = (to, from, next) => {
  if (!mapRoutesChildrenParent[from.name]) return next()
  const parentRoute = mapRoutesChildrenParent[from.name]
  if (to.name === parentRoute) {
    next((vm) => {
      const f = vm.goToRow
      const table = vm.$refs?.table
      if (f) {
        f(from.params.id)
      } else if (table && typeof table.goToRow === 'function') {
        table.goToRow(from.params.id)
      } else {
        // §B.10 — used to be a silent no-op. When the parent list component
        // lacks both a `goToRow` method and a `ref="table"` with that method,
        // navigation still proceeds (correct) but we surface a dev-only warning
        // so developers notice when a list-page lost its deep-link scroll.
        if (import.meta.env && import.meta.env.DEV) {
           
          console.warn(
            `[beforeRouteEnter] ${parentRoute} has neither vm.goToRow nor vm.$refs.table.goToRow; ` +
            `cannot restore row ${from.params.id} from ${from.name}.`
          )
        }
      }
    })
  } else next()
}

export { beforeRouteEnter }
