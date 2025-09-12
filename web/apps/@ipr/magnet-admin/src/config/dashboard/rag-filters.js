import store from '@/store'

const filter = {
  start_time: {
    label: 'Time period',
    key: 'start_time',

    type: 'timePeriod',
    default: 'P1D',
    overviewFilter: true,
  },
  feature_system_name: {
    label: 'RAG Tool',
    key: 'feature_system_name',
    get options() {
      return store.getters.chroma.rag_tools.items?.map((item) => ({ label: item.name, value: item.system_name })) ?? []
    },
    search: true,
    overviewFilter: true,
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
    overviewFilter: true,
  },
  consumer_name: {
    label: 'Consumer name',
    key: 'consumer_name',
    get options() {
      return store.getters.ragDashboardOptions?.consumer_names?.map((name) => ({ label: name, value: name })) ?? []
    },
    search: true,
    multiple: true,
    overviewFilter: true,
  },
  ['extra_data.topic']: {
    label: 'Topic',
    key: 'extra_data.topic',
    // is_hidden: true,
    //is_hideable: true,
    componentKey: 'topicOptions',
    options: () => {
      return store.getters.ragDashboardOptions?.topics?.map((topic) => ({ label: topic, value: topic }))
    },
  },
  ['extra_data.is_answered']: {
    label: 'Answered',
    key: 'extra_data.is_answered',
    options: [
      { label: 'Yes', value: true },
      { label: 'No', value: false },
      // { label: 'No Results', value: 'no_results' },
    ],
    hidden: true,
  },
  ['extra_data.answer_feedback.type']: {
    label: 'User feedback',
    key: 'extra_data.answer_feedback.type',
    options: [
      { label: 'Like', value: 'like' },
      { label: 'Dislike', value: 'dislike' },
    ],
  },

  ['extra_data.language']: {
    label: 'Language',
    key: 'extra_data.language',
    //is_hidden: true,
    //is_hideable: true,
    componentKey: 'languageOptions',
    options: () => {
      return store.getters.ragDashboardOptions?.languages?.map((language) => ({ label: language, value: language }))
    },
  },
      ['x_attributes.org-id']: {
      label: 'Organization',
      key: 'x_attributes.org-id',
      search: true,
      get options() {
        return store.getters.ragDashboardOptions?.organizations?.map((orgId) => ({ label: orgId, value: orgId })) ?? []
      },
    },
}

export default filter
