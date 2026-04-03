<template lang="pug">
div
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.common_notes() }}
    km-input(ref='input', rows='20', border-radius='8px', height='36px', type='textarea', v-model='notes')
    .km-description.text-secondary-text.q-pl-8.q-pt-4
      | {{ m.subtitle_storeSampleInput() }}
</template>

<script>
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
export default {
  setup() {
    const { activeVariant, updateVariantField } = useAgentEntityDetail()
    return { m, activeVariant, updateVariantField }
  },
  computed: {
    notes: {
      get() {
        return this.activeVariant?.value?.settings?.notes || ''
      },
      set(value) {
        this.updateVariantField('settings.notes', value)
      },
    },
  },
}
</script>
