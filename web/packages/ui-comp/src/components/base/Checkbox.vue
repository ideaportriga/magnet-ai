<template lang="pug">
q-checkbox(
  :size='size',
  color='primary',
  :val='val',
  @update:modelValue='$emit("update:modelValue", $event)',
  :model-value='modelValue',
  dense,
  :disable='disable',
  :class='{ "top-flex margin-checkbox": isAlignTop }'
)
  //.top-flex
  template(v-if='isSlotTaken')
    <slot/>
  template(v-else-if='chipped')
    .q-py-4.q-px-12.rounded-borders.checkbox-text.q-my-8(:style='{ background: chipColor, color: chipFontColor, fontSize: "12px" }') {{ displayText }}

  template(v-else-if='!!displayText')
    .text-secondary-text.checkbox-text.q-my-8(:style='{ overflow: "hidden", maxWidth: `${textMaxWidth}px`, textOverflow: "ellipsis" }') {{ displayText }}
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    modelValue: {},
    val: {},
    chipped: {
      type: Boolean,
      default: false,
    },
    displayText: {
      type: String,
      default: '',
    },
    chipColor: {
      type: String,
      default: '#D1D1D1',
    },
    chipFontColor: {
      type: String,
      default: '#5C5C5C',
    },
    disable: {
      type: Boolean,
      default: false,
    },
    size: {
      type: String,
      default: '32px',
    },
    textMaxWidth: {
      type: Number,
      default: 999999,
    },
    isAlignTop: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    isSlotTaken() {
      return !!this.$slots.default
    },
  },
})
</script>
<style lang="stylus">
.checkbox-text {
  line-height: 14px;
  font-size: 14px;
  font-weight: 500;
  font-stretch: 100;
  white-space: nowrap;
}

.margin-checkbox .q-checkbox__inner {
  margin-top: 4px;
}
</style>
