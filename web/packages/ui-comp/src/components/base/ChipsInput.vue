<template lang="pug">
span
  q-select.km-control.km-select.km-chips-input.rounded-borders.ba-border(
    ref='input',
    dropdown-icon='expand_more',
    :placeholder='placeholder',
    borderless,
    rounded,
    multiple,
    dense,
    use-chips,
    options-dense,
    options-selected-class='bg-primary-bg',
    popup-content-class='km-shadow border-radius-6',
    :options='pickOptions',
    :autogrow='autogrow',
    :hide-dropdown-icon='type === "add"',
    :model-value='modelValue',
    @update:modelValue='onUpdate',
    @remove='$emit("remove", $event)',
    @add='$emit("pick", $event)'
  )
    template(v-if='type === "add"', v-slot:append)
      q-icon.text-seemless.q-pr-8(name='fas fa-plus', size='18px', @click='$emit("add")')
    template(v-if='type !== "add"', #no-option)
      .km-label.q-pa-md.text-placeholder {{ noOptionText }}
  template(v-if='errorMessage')
    .km-small-chip.q-pa-4.q-pl-8.text-error-text {{ errorMessage }}
</template>

<script>
import { toRefs, ref } from 'vue'
import { useValidation, validationProps } from '@shared'

export default {
  props: {
    type: {
      type: String,
      default: 'pick', // "pick", "add"
    },
    modelValue: Array,
    placeholder: String,
    options: Array,
    noOptionText: {
      type: String,
      default: 'No Options available',
    },
    autogrow: {
      type: Boolean,
      default: false,
    },
    height: {
      default: '32px',
    },
    maxHeight: {
      default: 'unset',
    },
    minHeight: {
      default: '32px',
    },
    borderRadius: {
      type: String,
      default: '4px',
    },
    ...validationProps(),
  },
  emits: ['update:modelValue', 'chip:click', 'remove', 'add', 'pick', 'update:error'],
  setup(props) {
    const { modelValue, rules } = toRefs(props)
    return {
      popupShow: ref(false),
      ...useValidation(modelValue, rules),
    }
  },
  computed: {
    pickOptions() {
      return this.options || []
    },
    fieldSize() {
      return this.autogrow ? 'auto' : this.height
    },
  },
  mounted() {
    const selectElement = this.$refs.input.$el
    // Add a click event listener to the chips
    selectElement.addEventListener('click', this.handleChipClick)
  },
  methods: {
    onUpdate($event) {
      this.$emit('update:modelValue', $event)
      this.$emit('update:error', false)
    },
    handleChipClick(event) {
      const chip = event.target.closest('.q-chip')
      if (chip && !event.target.classList.contains('q-chip__remove')) {
        const value = chip.querySelector('.q-chip__content').textContent.trim()
        const index = this.modelValue.indexOf(value)
        this.$emit('chip:click', { index, value })
      }
    },
  },
}
</script>

<style lang="stylus" scoped>
.km-control {
  --field-height: v-bind(fieldSize) !important;
  --field-initial-height: v-bind(height) !important;
  --field--border-radius: v-bind(borderRadius) !important;
  --field-min-height: v-bind(minHeight);
  --field-max-height: v-bind(maxHeight);
}
</style>
