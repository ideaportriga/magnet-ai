import { getCachedItems } from '@/queries/getCachedItems'
import { useDashboardStore } from '@/stores/dashboardStore'

const filter = {
  start_time: {
    label: 'Time period',
    key: 'start_time',

    type: 'timePeriod',
    default: 'P1D',
    // overviewFilter: true,
  },
  feature_system_name: {
    label: 'Agent',
    key: 'feature_system_name',
    get options() {
      const dashboardStore = useDashboardStore()
      if (dashboardStore.agentDashboardOptions?.tools) {
        return getCachedItems('agents').map((item) => ({ label: item.name, value: item.system_name })) ?? []
      }
      return []
    },
    search: true,
    // overviewFilter: true,
  },
  source: {
    label: 'Consumer type',
    key: 'source',
    type: 'component',
    options: [
      { label: 'Runtime API', value: 'Runtime API' },
      { label: 'Runtime AI App', value: 'Runtime AI App' },
      { label: 'Preview', value: 'preview' },
      { label: 'Evaluation', value: 'evaluation' },
    ],
    multiple: true,
    default: ['Runtime AI App', 'Runtime API'],
    // overviewFilter: true,
  },
  consumer_name: {
    label: 'Consumer name',
    key: 'consumer_name',
    get options() {
      const dashboardStore = useDashboardStore()
      return dashboardStore.agentDashboardOptions?.consumer_names?.map((name) => ({ label: name, value: name })) ?? []
    },
    search: true,
    multiple: true,
    // overviewFilter: true,
  },
  ['extra_data.status']: {
    label: 'Status',
    key: 'extra_data.status',
    type: 'component',
    options: [
      // { label: 'Open', value: 'open' },
      { label: 'Closed', value: 'Closed' },
      { label: 'In Progress', value: 'In Progress' },
    ],
  },

  ['conversation_data.topics']: {
    label: 'Agent topic',
    key: 'conversation_data.topics',
    type: 'component',
    options: () => {
      const dashboardStore = useDashboardStore()
      if (dashboardStore.agentDashboardOptions?.topics) {
        return dashboardStore.agentDashboardOptions?.topics?.map((topic) => ({ label: topic, value: topic })) ?? []
      }
      return []
    },
    multiple: true,
  },
  ['conversation_data.resolution_status']: {
    label: 'Resolution status ',
    key: 'conversation_data.resolution_status',
    type: 'component',
    options: [
      { label: 'Resolved', value: 'resolved' },
      { label: 'Not resolved', value: 'not_resolved' },
      { label: 'Transferred to human', value: 'transferred' },
    ],
    multiple: true,
  },
  feedback: {
    label: 'User feedback',
    key: 'feedback',
    type: 'component',
    options: [
      { label: 'Liked', value: 'like' },
      { label: 'Disliked', value: 'dislike' },
    ],
    multiple: true,
    customLogic: (value) => {
      value = Array.isArray(value) ? value : [value]
      const filter = []
      if (value.some((item) => item.value === 'like')) {
        filter.push({ 'conversation_data.likes': { $gt: 0 } })
      }
      if (value.some((item) => item.value === 'dislike')) {
        filter.push({ 'conversation_data.dislikes': { $gt: 0 } })
      }
      return filter
    },
  },

  ['conversation_data.language']: {
    label: 'Language',
    key: 'conversation_data.language',
    type: 'component',
    options: () => {
      const dashboardStore = useDashboardStore()
      return dashboardStore.agentDashboardOptions?.languages?.map((language) => ({ label: language, value: language })) ?? []
    },
  },
  ['conversation_data.sentiment']: {
    label: 'Sentiment',
    key: 'conversation_data.sentiment',
    type: 'component',
    options: [
      { label: 'Positive', value: 'positive' },
      { label: 'Neutral', value: 'neutral' },
      { label: 'Negative', value: 'negative' },
    ],
  },
  ['x_attributes.org-id']: {
    label: 'Organization',
    key: 'x_attributes.org-id',
    search: true,
    get options() {
      const dashboardStore = useDashboardStore()
      return dashboardStore.agentDashboardOptions?.organizations?.map((orgId) => ({ label: orgId, value: orgId })) ?? []
    },
  },
}

export default filter
