<script setup lang="ts">
/**
 * One condition row inside the filter editor — equal/not-equal toggle plus
 * an input. Rewritten on `@ds`.
 */

import type { Condition } from '@shared/types'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmInput from '@ds/components/domain/KmInput.vue'

const condition = defineModel<Condition>({ required: true })
defineProps<{
  readonly?: boolean
  placeholder?: string
}>()
const emit = defineEmits<{ remove: [] }>()
</script>

<template>
  <div class="metadata-filter-condition cluster gap-sm" data-align="center" data-wrap="no">
    <div class="metadata-filter-condition__field">
      <KmInput
        v-model="condition.value"
        class="metadata-filter-condition__input"
        :class="{ 'is-readonly': readonly }"
        :readonly="readonly"
        :placeholder="placeholder"
      />
      <button
        type="button"
        class="metadata-filter-condition__operator"
        @click="condition.operator = condition.operator === 'equal' ? 'not-equal' : 'equal'"
      >
        {{ condition.operator === 'equal' ? '=' : '≠' }}
      </button>
    </div>
    <KmBtn flat icon="delete" icon-size="16px" @click="emit('remove')" />
  </div>
</template>

<style>
.metadata-filter-condition__field { position: relative; flex: 1 1 auto; min-inline-size: 0; }
.metadata-filter-condition__input .km-input__field { padding-inline-start: 30px; }
.metadata-filter-condition__input.is-readonly .km-input__field { font-style: italic; }

.metadata-filter-condition__operator {
  position: absolute;
  inset-block-start: 4px;
  inset-inline-start: 6px;
  inline-size: 25px;
  block-size: 25px;
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
  border: 0;
  border-radius: var(--ds-radius-sm);
  font-weight: var(--ds-font-weight-semibold);
  cursor: pointer;
  z-index: var(--ds-z-raised);
}
</style>
