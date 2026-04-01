<template lang="pug">
//- Collapsed sidebar: icon-only button with popup menu
template(v-if="sidebarCollapsed")
  .column.km-btn-expand-collapsed
    km-btn.width-100.border-radius-6.justify-center(
      :icon='item.icon',
      :icon-color='isShouldExpand ? `primary` : `icon`',
      :bg='isShouldExpand ? `primary-bg` : ``',
      icon-size='18px',
      :tooltip='item.label',
      flat
    )
    q-menu(anchor='top right', self='top left', :offset='[8, 0]')
      q-list(dense, style='min-width: 160px')
        q-item-label.text-primary.km-button-xs-text(header) {{ item.label }}
        q-item.km-nav-popup-item(
          v-for='(subItem, index) in subItems',
          :key='index',
          clickable,
          v-close-popup,
          :active='parentRoute.includes(subItem.path)',
          active-class='text-primary bg-primary-bg',
          @click='navigate(subItem.path)'
        )
          q-item-section(avatar)
            q-icon(:name='subItem.icon', size='14px', :color='parentRoute.includes(subItem.path) ? "primary" : "icon"')
          q-item-section
            span(:class='parentRoute.includes(subItem.path) ? "text-primary" : ""') {{ subItem.label }}

//- Expanded sidebar: normal expand/collapse behavior
template(v-else)
  .column.q-gap-8
    km-btn(
      :icon='item.icon',
      :label='item.label',
      :icon-color='isShouldExpand ? `primary` : `icon`',
      :bg='isShouldExpand ? `primary-bg` : ``',
      label-class='km-title',
      icon-size='16px',
      flat,
      @click='toggleExpansion',
      :icon-after='expanded ? "expand_less" : "expand_more"'
    )
    .q-pl-md.q-gap-8.column(v-if='expanded')
      km-btn(
        v-for='(subItem, index) in subItems',
        :key='index',
        :icon='subItem.icon',
        :label='subItem.label',
        :icon-color='parentRoute.includes(subItem.path) ? `primary` : `icon`',
        label-class='km-title',
        icon-size='16px',
        flat,
        @click='navigate(subItem.path)',
        :bg='parentRoute.includes(subItem.path) ? `primary-bg` : ``'
      )
</template>

<script>
export default {
  props: {
    item: {
      type: Object,
      required: true,
    },
    subItems: {
      type: Array,
      default: () => [],
    },
    sidebarCollapsed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      expanded: false,
    }
  },
  computed: {
    isShouldExpand() {
      return this.subItems.some((subItem) => subItem.path == this.parentRoute)
    },
    parentRoute() {
      return this.$route?.path
    },
  },
  mounted() {
    this.checkIfShouldExpand()
  },
  methods: {
    checkIfShouldExpand() {
      this.expanded = this.isShouldExpand
    },
    toggleExpansion() {
      this.expanded = !this.expanded
      if (this.expanded) {
        this.$router.push('/' + this.subItems[0].path)
      }
    },
    navigate(path) {
      this.$router.push('/' + path)
    },
  },
}
</script>
