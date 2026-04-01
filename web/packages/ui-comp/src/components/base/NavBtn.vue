<template>
  <km-btn
    v-if="!sidebarCollapsed"
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
  <km-btn
    v-else
    :data-test="`nav-btn-${label}`"
    :class="['width-100', 'border-radius-6', 'justify-center', { 'bg-primary-bg': isActive, 'color-primary': isActive, 'iconColor-primary': isActive }]"
    :icon="icon"
    :icon-color="isActive ? 'primary' : 'icon'"
    :hover-color="isActive ? 'primary' : 'primary'"
    :hover-bg="isActive ? 'primary-bg' : 'primary-bg'"
    icon-size="18px"
    :tooltip="label"
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
    alternativePaths: {
      type: Array as PropType<string[]>,
      default: () => [],
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
    sidebarCollapsed: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['navigate'],
  computed: {
    isActive() {
      const mainPathActive = this.parentRoute === `/${this.path}`
      const aiAppsActive = this.parentRoute === `/` && this.label === 'AI Apps'
      const alternativePathsActive = this.alternativePaths?.some((altPath: string) => this.parentRoute === `/${altPath}`)

      return mainPathActive || aiAppsActive || alternativePathsActive
    },
  },
  methods: {
    navigate() {
      this.$emit('navigate', this.path)
    },
  },
})
</script>
