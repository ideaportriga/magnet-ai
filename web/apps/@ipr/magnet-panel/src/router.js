import { createRouter, createWebHashHistory } from 'vue-router'

import LayoutTab from '@/components/LayoutTab.vue'

const routes = [
  {
    path: '/',
    name: 'Panel',
    component: LayoutTab,
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// router.beforeEach((to, from, next) => {
//   if (store.getters.showLeaveConfirm) {
//     store.commit('setIsNavigationCancelled', false)
//     next()
//   }
//   if (
//     (from.name === 'ConfigurationItems' && store.getters.isRagChanged) ||
//     (from.name === 'RetrievalItems' && store.getters.isRetrievalChanged) ||
//     (from.name === 'EvaluationSetDetails' && store.getters.isEvaluationSetChanged) ||
//     (from.name === 'PromptTemplatesItem' && store.getters.isPromptTemplateChanged) ||
//     (from.name === 'AIAppDetail' && store.getters.isAIAppChanged)
//   ) {
//     store.commit('setNextRoute', to.fullPath)
//     store.commit('showPopup')
//     store.commit('setIsNavigationCancelled', true)
//     next(false)
//   } else {
//     store.commit('setIsNavigationCancelled', false)
//     next()
//   }
// })

// router.afterEach(async (to) => {
//   if (store.getters.isNavigationCancelled) {
//     return
//   }
//   const query = to.query ?? {}

//   store.commit('set', {
//     ...(query.sourceSystem ? { sourceSystem: query.sourceSystem } : {}),
//     ...(query.viewMode ? { viewMode: query.viewMode } : {}),
//     ...(query.agentRecordId ? { agentRecordId: query.agentRecordId } : {}),
//     ...(query.agentObjectType ? { agentObjectType: query.agentObjectType } : {}),
//     ...(query.sourceSystemUserName ? { sourceSystemUserName: query.sourceSystemUserName } : {}),
//   })
// })

export default router
