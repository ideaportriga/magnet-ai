<template lang="pug">
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
      // const segments = this.$route?.path?.split('/')
      // return `${segments?.[1]}`
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
