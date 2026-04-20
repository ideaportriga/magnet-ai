<template lang="pug">
.km-drawer-layout.bg-white.bl-border.km-side-drawer(:style='drawerStyle')
  km-drawer-resize-handle(@mousedown='onResizeStart')
  //- Header slot (title, back button, etc.)
  .km-drawer-header.q-px-16.q-pt-16(v-if='$slots.header')
    slot(name='header')
    q-separator.q-mt-12
  //- Tabs slot (alternative to header)
  .km-drawer-tabs(v-if='$slots.tabs')
    slot(name='tabs')
  //- Content — single flex-grow slot so the scroll/plain branches share
  //- the same sizing. q-scroll-area manages its own scrollbar; plain
  //- branch uses native overflow.
  .km-drawer-content(v-if='!noScroll')
    q-scroll-area.fit.q-px-16.q-py-16
      slot
  .km-drawer-content.km-drawer-content--plain.q-px-16.q-py-16(v-else)
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

<style lang="stylus" scoped>
// Flex column with explicit shrink flags per named slot.
//
// Grid was tried before (grid-template-rows: auto auto minmax(0,1fr) auto)
// but auto-placement is positional: with 4 fixed rows and optional
// children (v-if on header/tabs/footer), a missing slot shifts content
// into the wrong row. When content lands in an `auto` row it grows to
// its intrinsic height and the footer (placed into the 1fr row) gets
// compressed to 0. Flex makes the "which slot shrinks" decision
// per-element instead of positional: only `.km-drawer-content`
// flex-grows and can shrink below its content; header/tabs/footer are
// `flex: 0 0 auto` so they keep their intrinsic height and stay
// on-screen no matter which combination of slots renders.
//
// Height contract: parent must give this element a bounded height
// (e.g. `.col-auto.full-height` in a `.row.full-height.overflow-hidden`).
// No `max-height: 100vh` band-aid — if the chain is sound, it's
// redundant; if it's broken, clamping to viewport just hides the bug.
.km-drawer-layout
  display: flex
  flex-direction: column
  height: 100%
  overflow: hidden
  position: relative

.km-drawer-header,
.km-drawer-tabs,
.km-drawer-footer
  flex: 0 0 auto

.km-drawer-content
  flex: 1 1 0
  min-height: 0
  position: relative

.km-drawer-content--plain
  overflow: auto
</style>
