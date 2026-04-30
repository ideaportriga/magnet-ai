<template>
  <div>
    <div class="km-field text-secondary-text pb-sm pl-sm">
      {{ m.common_notes() }}
      <km-input ref="input" v-model="notes" rows="20" border-radius="8px" height="36px" type="textarea" />
      <div class="km-description text-secondary-text pl-sm pt-xs">{{ m.subtitle_storeSampleInput() }}</div>
    </div>
  </div>
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
