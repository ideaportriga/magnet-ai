<template lang="pug">
div
  km-section(:title='m.section_notes()', :subTitle='m.subtitle_storeSampleInput()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_notes() }}
    km-input(ref='input', rows='20', :placeholder='m.prompts_typeYourText()', border-radius='8px', height='36px', type='textarea', v-model='sampleText')
</template>

<script>
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { m } from '@/paraglide/messages'

export default {
  setup() {
    const { activeVariant, updateVariantField } = useVariantEntityDetail('promptTemplates')
    return { m, activeVariant, updateVariantField }
  },
  computed: {
    sampleText: {
      get() {
        return this.activeVariant?.sample_text || ''
      },
      set(value) {
        this.updateVariantField('sample_text', value)
      },
    },
  },
}
</script>
