<template lang="pug">
template(v-if='name === "three-body"')
  .three-body(:style='cssVars')
    .three-body__dot
    .three-body__dot
    .three-body__dot
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    name: {
      type: String,
      default: 'three-body',
    },
    size: {
      type: String,
      default: '35px',
    },
    speed: {
      type: String,
      default: '1.1s',
    },
    color: {
      type: String,
      default: 'primary',
    },
  },
  emits: ['update:modelValue'],
  computed: {
    cssVars() {
      return {
        '--uib-size': this.size,
        '--uib-speed': this.speed,
        '--uib-color': `var(--q-${this.color})`,
      }
    },
  },
})
</script>
<style lang="stylus"></style>
