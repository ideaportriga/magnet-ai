<template>
  <div>
    <km-section :title="m.section_notes()" :sub-title="m.subtitle_storeSampleInput()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_notes() }}</div>
      <km-input ref="input" v-model="sampleText" rows="20" :placeholder="m.prompts_typeYourText()" border-radius="8px" height="36px" type="textarea" />
    </km-section>
  </div>
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
