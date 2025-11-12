<template lang="pug">
.km-control.km-button-icon.center-flex.rounded-borders(:class='{ "no-pointer-events": disabled }')
  q-icon(:name='icon', :size='iconSize', :class='`text-${color}`')
</template>

<script lang="ts">
export default {
  props: {
    color: {
      type: String,
      default: 'icon',
    },
    icon: {
      type: String,
      default: 'autorenew',
    },
    height: {
      type: String,
    },
    width: {
      type: String,
    },
    bg: {
      type: String,
      default: 'transparent',
    },
    disabled: {
      type: Boolean,
    },
    iconSize: {
      type: String,
      default: '24px',
    },
  },
}
</script>

<style lang="stylus" scoped>
.km-button-icon {
  cursor: pointer;
  height: v-bind(height);
  width: v-bind(height);
  background: v-bind(bg);

  &:hover {
    transition: all 200ms linear;
    transform: translateY(-1px);
    background: v-bind(bg);

    .q-icon {
      transition: all 200ms linear;
      color: var(--q-primary) !important
    }
  }

  &:hover:before {
    transition: all 200ms linear;
  }
}
</style>
