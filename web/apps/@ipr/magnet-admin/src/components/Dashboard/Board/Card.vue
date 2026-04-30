<template>
  <div class="stack ba-border border-radius-12 p-lg fit" data-gap="0" v-bind="$attrs" :class="`bg-${themeStyle.bg} ba-${themeStyle.border}`">
    <div class="cluster pb-md" :class="`bb-${themeStyle.border}`" data-justify="between">
      <slot name="header">
        <div class="flex-1">
          <div class="cluster" data-gap="xs">
            <div class="km-title text-dashboard-heading">{{ header }}</div>
            <km-glyph v-if="tooltip" class="flex-none ml-xs" name="info">
              <km-tooltip class="bg-white block-shadow km-description" self="top middle" :offset="[-50, -50]">
                <div class="text-secondary-text">{{ tooltip }}</div>
              </km-tooltip>
            </km-glyph>
          </div>
        </div>
        <div v-if="headerAction" class="flex-none">
          <km-btn flat icon="chevron-right" icon-size="14px" tone="subtle" size="xs" @click="headerAction" />
        </div>
      </slot>
    </div>
    <div class="stack fit pt-lg" data-gap="0">
      <slot name="body">
        <div class="km-paragraph">{{ body }}</div>
      </slot>
    </div>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
export default {
  props: {
    header: {
      type: String,
      default: 'Default Header',
    },
    body: {
      type: String,
      default: 'Default Body Content',
    },
    headerAction: {
      type: Function,
      default: null,
    },
    theme: {
      type: String,
      default: 'light',
    },
    tooltip: String,
  },
  computed: {
    themeStyle() {
      if (typeof this.theme !== 'string') {
        return this.theme
      }
      if (this.theme === 'dark') {
        return {
          bg: 'table-header',
          border: 'border-2',
        }
      }
      if (this.theme === 'muted') {
        return {
          bg: 'border',
          border: 'border',
        }
      }
      return {
        bg: 'white',
        border: 'border',
      }
    },
  },
}
</script>
