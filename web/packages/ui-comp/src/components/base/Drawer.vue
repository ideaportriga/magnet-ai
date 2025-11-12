<template lang="pug">
//- have to be used inside row with no wrap and overflow hidden

.km-drawer-fake(v-if='!fixed', :style='{ minWidth: modelValue ? width : "0px" }')
.km-drawer
  .km-drawer-container(:style='{ width, transform: `translateX(${modelValue ? "-100%" : "0%"})` }') 
    q-scroll-area.height-100.bg-white
      slot
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  emit: ['update:modelValue'],
  props: {
    width: {
      type: String,
      default: '500px',
    },
    fixed: {
      type: Boolean,
      default: false,
    },
    modelValue: {
      type: Boolean,
      default: false,
    },
  },
  setup() {},
})
</script>
<style lang="stylus">
.km-drawer
    width: 0px;
    &-fake{
        transition: 1s;
    }
    &-container
        transition: 1s;
        width: 0px
        right: 0;
        height: 100%
</style>
