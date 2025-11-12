<template lang="pug">
.column.ba-border.border-radius-12.q-pa-16.no-wrap.fit(v-bind='$attrs', :class='`bg-${themeStyle.bg} ba-${themeStyle.border}`')
  .row.justify-between.items-center.q-pb-12.items-center(:class='`bb-${themeStyle.border}`')
    slot(name='header')
      .col
        .row.items-center.q-gap-4
          .km-title.text-dashboard-heading {{ header }}
          q-icon.col-auto.q-ml-4(name='o_info', color='secondary', v-if='tooltip')
            q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]')
              .text-secondary-text {{ tooltip }}
      .col-auto(v-if='headerAction')
        km-btn(flat, icon='fas fa-chevron-right', iconSize='14px', color='secondary-text', size='xs', @click='headerAction')
  .column.fit.q-pt-16
    slot(name='body')
      .km-paragraph {{ body }}
</template>

<script>
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
      return {
        bg: 'white',
        border: 'border',
      }
    },
  },
}
</script>
