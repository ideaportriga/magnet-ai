<template lang="pug">
div
  km-section(title='Notes', subTitle='Store your sample input here and copy to preview area')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Notes
    km-input(ref='input', rows='20', placeholder='Type your text here', border-radius='8px', height='36px', type='textarea', v-model='sampleText')
</template>

<script>
export default {
  computed: {
    sampleText: {
      get() {
        return this.$store.getters.promptTemplateVariant?.sample_text || ''
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'sample_text', value })
      },
    },
  },
}
</script>
