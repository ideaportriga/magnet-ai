<template>
  <div class="stack mt-2xl width-100 border-radius-6" data-gap="sm">
    <div class="km-chip text-secondary text-uppercase">
      <div class="cluster">
        <km-btn class="flex-none" :icon="&quot;chevron-left&quot;" icon-size="16px" icon-tone="subtle" flat @click="navigate(&quot;knowledge-sources&quot;)" />
        <div class="flex-1">{{ m.common_knowledgeSources() }}</div>
      </div>
      <km-separator />
    </div>
    <template v-for="item in knowledge" :key="item">
      <km-btn class="width-100" :selected="routerMetaName === item.name" :label-class="&quot;km-title&quot;" :icon="item.icon" :label="item.label" flat icon-size="14px" interaction-tone="brand" @click="navigate(item.path)" />
    </template>
  </div>
</template>

<script lang="ts">
import { useAuth } from '@shared'
import { m } from '@/paraglide/messages'

export default {
  setup() {
    const { logout } = useAuth()
    return {
      m,
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
          label: m.common_configurations(),
          icon: 'settings',
          path: `knowledge-sources/${this.id}`,
        },
        {
          name: 'CollectionItems',
          label: m.common_chunks(),
          icon: 'menu',
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

<style scoped>
.km-toolbar {
  overflow: scroll;
  inline-size: 100%;
  box-sizing: border-box;
}
</style>
