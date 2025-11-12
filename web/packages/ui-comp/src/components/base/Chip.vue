<template lang="pug">
.inline-block.vertical-middle.position-chip(
  @mouseenter='hover = true',
  @mouseleave='hover = false',
  :class='chipClass',
  :style='[flatColor ? { background: color } : {}, round ? " border-radius: 12px" : "border-radius: var(--chip-radius)"]'
)
  .row.no-wrap.text-no-wrap.items-center.full-height
    slot.col-auto.text-overflow-ellipsis
    .col-auto.center-flex-y(style='position: relative')
      q-icon(v-if='icon', :name='icon', :size='iconSize', tag='div', :color='iconColor', :style='{ "margin-right": iconMarginRight }')
    .col-auto.text-overflow-ellipsis(v-if='label', :class='labelClass') {{ label }}

  template(v-if='tooltip')
    km-tooltip(:label='tooltip')
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    size: {
      type: String,
      default: '24px',
    },
    iconSize: {
      type: String,
      default: '20px',
    },
    iconColor: {
      type: String,
      default: '',
    },
    iconMarginRight: {
      type: String,
      default: '12px',
    },
    icon: {
      type: String,
      default: '',
    },
    label: {
      type: String,
      default: '',
    },
    tooltip: {
      type: String,
      default: '',
    },
    labelClass: {
      type: String,
      default: 'km-heading',
    },
    clickable: {
      type: Boolean,
    },
    round: {
      type: Boolean,
    },
    color: {
      type: String,
    },
    flatColor: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    return {
      hover: ref(false),
    }
  },
  computed: {
    chipClass() {
      const clickableClass = {
        'cursor-pointer position-chip-normal': this.clickable,
      }
      const colorClass = {
        ['bg-' + this.color]: !!this.color && !this.flatColor,
      }

      const padding = {
        'q-px-sm': this.color ? true : false,
      }

      return { ...clickableClass, ...colorClass, ...padding }
    },
  },
}
</script>

<style lang="stylus" scoped>
.position-chip {
  height: v-bind(size);
  background-color: transparent;
}

.position-chip-selected {
  @extend .position-chip;
  transition: background-color 1s ease-out;
}

.position-chip-normal {
  @extend .position-chip;
  transition: background 300ms;

  &:hover {
    background: var(--q-accent-bg) !important;
    cursor: pointer;
  }

  &:active {
    background: var(--q-accent-bg) !important;
  }
}
</style>
