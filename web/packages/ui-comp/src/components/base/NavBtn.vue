<template>
  <km-btn
    :data-test="`nav-btn-${label}`"
    :class="['width-100', 'border-radius-6', { 'bg-primary-bg': isActive, 'color-primary': isActive, 'iconColor-primary': isActive }]"
    :icon="icon"
    :label="label"
    :icon-color="isActive ? 'primary' : 'icon'"
    :hover-color="isActive ? 'primary' : 'primary'"
    :hover-bg="isActive ? 'primary-bg' : 'primary-bg'"
    :label-class="labelClass"
    :icon-size="iconSize"
    flat
    @click="navigate"
  />
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'

export default defineComponent({
  props: {
    icon: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    path: {
      type: String,
      required: true,
    },
    parentRoute: {
      type: String,
      required: true,
    },
    labelClass: {
      type: String,
      default: 'km-heading-2',
    },
    iconSize: {
      type: String,
      default: '14px',
    },
  },
  computed: {
    isActive() {
      return this.parentRoute === `/${this.path}` || this.parentRoute === `/` && this.label === 'AI Apps'
    },
  },
  methods: {
    navigate() {
      this.$emit('navigate', this.path)
    },
  },
})
</script>


   km-btn.width-100(
      bg='primary-bg',
      color='primary',
      iconColor='primary',
      labelClass='km-heading-2',
      :icon='item.icon',
      :label='item.label',
      @click='navigate(item.path)',
      flat,
      iconSize='14px',
      hoverBg='primary-bg'
    )
  template(v-else)
    km-btn.width-100(
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-heading-2',
      :icon='item.icon',
      :label='item.label',
      @click='navigate(item.path)',
      flat,
      iconSize='14px',
      hoverBg='primary-bg'
    )