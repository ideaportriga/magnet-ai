<template lang="pug">
.row.switch-button-container.rounded-borders(:class='[`bg-${this.backgroundColor}`]')
  template(v-for='(option, i) in options')
    q-btn(
      :unelevated='true',
      :rounded='false',
      :padding='`${this.padding}px`',
      :size='"12px"',
      @click='$emit("update:modelValue", option.value)',
      :class='[option.value === modelValue ? "bg-secondary text-primary" : "text-secondary-text", "switch-button", i === 0 ? "first-element" : i === options.length - 1 ? "last-element" : "center-element"]',
      :style='{ width, height }',
      dense
    )
      .row.center-flex-y
        template(v-if='option.icon')
          q-icon.q-mr-sm(size='22px', :name='option.icon')
        .col
          .km-chip {{ option.label }}
</template>
<script>
export default {
  props: {
    options: {
      type: Array,
      default: () => [],
    },
    size: {
      type: Number,
      default: 36,
    },
    backgroundColor: {
      type: String,
      default: 'background',
    },
    color: {
      type: String,
      default: '#ffffff',
    },
    padding: {
      type: Number,
      default: 6,
    },
    modelValue: {
      default: 0,
    },
    width: {
      default: 'auto',
    },
    height: {
      default: 'auto',
    },
  },
  emits: ['update:modelValue'],
  setup() {},
}
</script>

<style lang="scss">
.switch-button * {
  text-transform: none;
}
</style>

<style lang="stylus" scoped>
.first-element {
  border-top-left-radius: 4px;
  border-bottom-left-radius: 4px;
  border-top-right-radius: 0px;
  border-bottom-right-radius: 0px;
}

.last-element {
  border-top-left-radius: 0px;
  border-bottom-left-radius: 0px;
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
}

.center-element {
  border-radius: 0px;
}
</style>
