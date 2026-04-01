<template lang="pug">
div
  km-section(title='Type', subTitle='Type of objects that the Test Set will be used for')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
    km-select(
      height='auto',
      minHeight='36px',
      placeholder='Type',
      :options='[ { value: "rag_tool", label: "RAG" }, { value: "prompt_template", label: "Prompt Template" }, ]',
      v-model='type',
      ref='typeRef',
      option-value='value',
      emit-value,
      map-options
    )
</template>

<script>
import { useEvaluationSetDetailStore } from '@/stores/entityDetailStores'

export default {
  emits: ['openTest'],
  setup() {
    const evalSetStore = useEvaluationSetDetailStore()
    return { evalSetStore }
  },
  computed: {
    type: {
      get() {
        return this.evalSetStore.entity?.type || ''
      },
      set(value) {
        this.evalSetStore.updateProperty({ key: 'type', value })
      },
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
