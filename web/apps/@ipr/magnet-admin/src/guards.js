const mapRoutesChildrenParent = {
  ApiToolsDetails: 'ApiTools',
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
      } else if (table) {
        table.goToRow(from.params.id)
      } else {
        console.log('goToRow not found')
      }
    })
  } else next()
}

export { beforeRouteEnter }
