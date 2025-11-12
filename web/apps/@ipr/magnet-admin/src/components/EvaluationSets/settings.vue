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
export default {
  emits: ['openTest'],
  computed: {
    type: {
      get() {
        return this.$store.getters.evaluation_set?.type || ''
      },
      set(value) {
        this.$store.commit('updateEvaluationSetProperty', { key: 'type', value })
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
