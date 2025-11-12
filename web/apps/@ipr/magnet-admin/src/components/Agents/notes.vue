<template lang="pug">
div
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 Notes
    km-input(ref='input', rows='20', border-radius='8px', height='36px', type='textarea', v-model='notes')
    .km-description.text-secondary-text.q-pl-8.q-pt-4
      | Store your sample input here and copy to preview area
</template>

<script>
export default {
  computed: {
    notes: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.notes || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.notes', value })
      },
    },
  },
}
</script>
