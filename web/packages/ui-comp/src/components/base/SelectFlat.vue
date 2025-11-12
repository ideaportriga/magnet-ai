<template lang="pug">
.select-container
  km-chip.q-py-4.q-px-6(clickable)
    .km-label.line-height-default {{ selectedOption }}
    q-icon.text-seemless.transition-default(name='expand_more', size='20px', :style='{ transform: `rotate(${open ? `180deg` : 0})` }')
  q-menu(fit, v-model='open', ref='menu')
    template(v-for='option in options')
      template(v-if='!hideOption(option)')
        slot(name='option', :option='option', :modelValue='modelValue', :select='select', :itemProps='itemProps')
          .km-label.q-px-md.q-py-6.cursor-pointer.hover-bg-light.cursor-pointer(
            @click='select(option)',
            :class='{ "bg-light": option.value === modelValue.value }'
          ) {{ option.label }}
</template>
<script>
import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: {
    placeholder: {},
    modelValue: {},
    options: {
      type: Array,
      default: () => [],
    },
    hideSelected: {
      type: Boolean,
      default: false,
    },
    itemProps: {
      type: Object,
      default: () => ({
        class: 'cursor-pointer hover-bg-light',
      }),
    },
    showLabel: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  setup() {
    return {
      open: ref(false),
    }
  },
  computed: {
    selectedOption() {
      if (!this.modelValue) return this.placeholder
      if (this.showLabel) return this.options?.find((option) => option.value === this.modelValue)?.label
      if (typeof this.modelValue === 'string') return this.modelValue
      return this.modelValue.label
    },
  },
  methods: {
    select(option) {
      this.$emit('update:modelValue', option)
      this.$refs.menu.hide()
    },
    hideOption(option) {
      if (!this.hideSelected) return false
      return option.value === this.selectedOption
    },
  },
})
</script>
