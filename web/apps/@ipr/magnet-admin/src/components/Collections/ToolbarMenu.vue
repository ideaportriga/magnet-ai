<template lang="pug">
.column.q-mt-24.width-100.q-gap-12.border-radius-6
  .km-chip.text-secondary.text-uppercase
    .row.items-center
      km-btn.col-auto(:icon='"fas fa-chevron-left"', @click='navigate("knowledge-sources")', iconSize='16px', iconColor='secondary-text', flat)
      .col Knowledge sources
    km-separator 
  template(v-for='item in knowledge')
    km-btn.width-100(
      :bg='routerMetaName === item.name ? "primary-bg" : undefined',
      :color='routerMetaName === item.name ? "primary" : undefined',
      :iconColor='routerMetaName === item.name ? "primary" : "icon"',
      :labelClass='"km-title"',
      :icon='item.icon',
      :label='item.label',
      @click='navigate(item.path)',
      flat,
      iconSize='14px',
      hoverBg='primary-bg',
      :hoverColor='routerMetaName !== item.name ? "primary" : undefined'
    )
</template>

<script lang="ts">
import { useAuth } from '@shared'

export default {
  setup() {
    const { logout } = useAuth()
    return {
      logout,
    }
  },
  computed: {
    id() {
      return this.$route.params.id
    },
    routerMetaName() {
      return this.$route.name || ''
    },
    knowledge() {
      return [
        {
          name: 'CollectionDetail',
          label: 'Configuration',
          icon: 'fas fa-gear',
          path: `knowledge-sources/${this.id}`,
        },
        {
          name: 'CollectionItems',
          label: 'Chunks',
          icon: 'fas fa-bars',
          path: `knowledge-sources/${this.id}/items`,
        },
      ]
    },
    parentRoute() {
      const segments = this.$route?.path?.split('/')
      return `/${segments?.[1]}`
    },
    isAdmin() {
      return this.$route.meta?.admin
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
  },
}
</script>

<style lang="stylus" scoped>
.km-toolbar {
  overflow: scroll;
  width: 100%;
  box-sizing: border-box;
}

.km-toolbar::-webkit-scrollbar {
  width: 4px;
}
</style>
