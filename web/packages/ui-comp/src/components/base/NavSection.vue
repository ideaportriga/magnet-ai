<template lang="pug">
//- Collapsed sidebar: single icon button with popup menu listing all items
template(v-if="sidebarCollapsed")
  .column.width-100.km-nav-section-collapsed
    km-btn.width-100.border-radius-6.justify-center(
      :icon='icon',
      :icon-color='hasActiveItem ? "primary" : "icon"',
      :bg='hasActiveItem ? "primary-bg" : ""',
      icon-size='18px',
      :tooltip='label',
      flat
    )
    q-menu(anchor='top right', self='top left', :offset='[8, 0]')
      q-list(dense, style='min-width: 180px')
        q-item-label.text-secondary.km-button-xs-text.text-uppercase(header) {{ label }}
        q-item.km-nav-popup-item(
          v-for='(item, index) in items',
          :key='index',
          clickable,
          v-close-popup,
          :active='isItemActive(item)',
          active-class='text-primary bg-primary-bg',
          @click='$emit("navigate", item.path)'
        )
          q-item-section(avatar, style='min-width: 28px; padding-right: 4px')
            q-icon(:name='item.icon', size='14px', :color='isItemActive(item) ? "primary" : "icon"')
          q-item-section
            span(:class='isItemActive(item) ? "text-primary" : ""') {{ item.label }}

//- Expanded sidebar: collapsable section with header
template(v-else)
  .column.width-100(:class="collapsed ? 'q-gap-2' : 'q-gap-6'")
    .row.items-center.cursor-pointer.q-px-4.km-nav-section-header(
      @click="$emit('toggle')"
    )
      .km-button-xs-text.text-secondary.text-uppercase {{ label }}
      q-space
      q-icon.text-secondary(
        :name="collapsed ? 'expand_more' : 'expand_less'"
        size="14px"
      )
    km-separator(v-if="!collapsed")
    template(v-if="!collapsed")
      slot
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'

interface NavItem {
  label: string
  icon: string
  path: string
  alternativePaths?: string[]
}

export default defineComponent({
  name: 'KmNavSection',
  props: {
    label: {
      type: String,
      required: true,
    },
    icon: {
      type: String,
      default: 'fas fa-folder',
    },
    items: {
      type: Array as PropType<NavItem[]>,
      default: () => [],
    },
    collapsed: {
      type: Boolean,
      default: false,
    },
    sidebarCollapsed: {
      type: Boolean,
      default: false,
    },
    parentRoute: {
      type: String,
      default: '',
    },
  },
  emits: ['toggle', 'navigate'],
  computed: {
    hasActiveItem(): boolean {
      return this.items.some((item: NavItem) => this.isItemActive(item))
    },
  },
  methods: {
    isItemActive(item: NavItem): boolean {
      const mainActive = this.parentRoute === `/${item.path}`
      const rootActive = this.parentRoute === '/' && item.label === 'AI Apps'
      const altActive = item.alternativePaths?.some((p: string) => this.parentRoute === `/${p}`) || false
      return mainActive || rootActive || altActive
    },
  },
})
</script>
