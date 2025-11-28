<template lang="pug">
.card.column.items-center.q-gap-8.q-px-md.q-py-lg.ba-border.border-radius-6(@mouseenter='hover = true', @mouseleave='hover = false')
  q-icon(:name='icon', width='16px', height='16px', color='primary')
  .row
    .km-heading-4.text-center.text-primary.q-mr-xs(v-if='qty') {{ qty }}
    .km-heading-4.text-center {{ label }}
  .km-field.text-center {{ description }}
  km-btn(v-if='hover && actionLabel', :label='actionLabel', @click='$emit("click")')
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Card',
  props: {
    icon: {
      type: String,
      default: 'fas fa-user',
    },
    label: {
      type: String,
      default: 'Configure your Agent',
    },
    description: {
      type: String,
      default: 'Make sure your Agent has all the essential parts to start working!',
    },
    actionLabel: {
      type: String,
      default: '',
    },
    qty: {
      type: Number,
      default: 0,
    },
  },
  emits: ['click'],
  setup() {
    return {
      hover: ref(false),
    }
  },
}
</script>

<style lang="scss" scoped>
.card {
  min-height: 182px;
}

.card:hover {
  // #C5BFEC 30%
  background-color: rgba(197, 191, 236, 0.3);
  cursor: pointer;
}
</style>
>
