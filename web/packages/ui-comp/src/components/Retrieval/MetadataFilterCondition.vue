<template>
  <div class="row q-gap-8">
    <km-input
      v-model="condition.value"
      :class="[{ 'text-italic': readonly }, 'col-grow', 'condition-input']"
      :readonly="readonly"
      :placeholder="placeholder"
      @change="condition.value = $event.target.value"
    />
    <div class="row items-center justify-center q-gap-8 absolute" style="margin-top: 4px; left: 6px">
      <q-btn
        class="operation-button"
        :label="condition.operator === 'equal' ? '=' : '≠'"
        color="primary"
        padding="0"
        size="md"
        @click="condition.operator = condition.operator === 'equal' ? 'not-equal' : 'equal'"
      />
    </div>
    <km-btn icon="far fa-trash-can" icon-size="16px" flat @click="emit('remove')" />
  </div>
</template>

<script setup lang="ts">
import type { Condition } from '@shared/types'

// Models & Props
const condition = defineModel<Condition>({ required: true })
defineProps<{
  readonly?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'remove'): void
}>()
</script>

<style lang="stylus" scoped>
.operation-button
  width: 25px
  height: 25px
</style>
