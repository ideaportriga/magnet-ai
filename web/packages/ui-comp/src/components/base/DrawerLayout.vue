<template lang="pug">
.km-drawer-layout.column.no-wrap.bg-white.bl-border.full-height.km-side-drawer(:style='drawerStyle')
  km-drawer-resize-handle(@mousedown='onResizeStart')
  //- Header slot (title, back button, etc.)
  .km-drawer-header.q-px-16.q-pt-16(v-if='$slots.header')
    slot(name='header')
    q-separator.q-mt-12
  //- Tabs slot (alternative to header)
  .km-drawer-tabs(v-if='$slots.tabs')
    slot(name='tabs')
  //- Content
  q-scroll-area.col.km-drawer-content.q-px-16.q-py-16(v-if='!noScroll')
    slot
  .col.km-drawer-content.q-px-16.q-py-16.overflow-auto(v-else)
    slot
  //- Footer slot (fixed at bottom, outside scroll area)
  .km-drawer-footer(v-if='$slots.footer')
    slot(name='footer')
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useDrawerResize } from '../../composables/useDrawerResize'

export default defineComponent({
  name: 'KmDrawerLayout',
  props: {
    storageKey: {
      type: String,
      required: true,
    },
    defaultWidth: {
      type: Number,
      default: 500,
    },
    minWidth: {
      type: Number,
      default: 320,
    },
    maxWidth: {
      type: Number,
      default: 900,
    },
    noScroll: {
      type: Boolean,
      default: false,
    },
  },
  setup(props) {
    const { drawerStyle, onResizeStart } = useDrawerResize({
      storageKey: props.storageKey,
      defaultWidth: props.defaultWidth,
      minWidth: props.minWidth,
      maxWidth: props.maxWidth,
    })

    return {
      drawerStyle,
      onResizeStart,
    }
  },
})
</script>
