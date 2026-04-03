<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading')
  km-inner-loading(:showing='loading')
.row.no-wrap.overflow-hidden.full-height(v-else)
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .q-my-lg
        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md(style='max-height: calc(100vh - 210px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  .col-auto.full-width
                    agents-topic-details-prompts
                    q-separator.q-my-lg
                    agents-topic-details-actions
</template>

<script>
import { ref, computed, onActivated } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const id = ref(route.params.id)
    onActivated(() => { id.value = route.params.id })
    const { data: selectedRow } = queries.agents.useDetail(id)
    const { options: items } = useCatalogOptions('agents')
    const removeMutation = queries.agents.useRemove()
    const { draft, activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
    return {
      draft,
      activeVariant,
      updateNestedListItemBySystemName,
      tab: ref('prompts'),
      tabs: ref([
        { name: 'actions', label: 'Actions' },
        { name: 'prompts', label: 'Topic instructions' },
      ]),
      showNewDialog: ref(false),
      activeAgentDetail: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      selectedRow,
      items,
      removeMutation,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    agentName() {
      return this.draft?.name
    },
    agentId() {
      return this.draft?.id
    },
    name: {
      get() {
        return this.topic?.name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            name: value,
          },
        })
      },
    },
    description: {
      get() {
        return this.topic?.description || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            description: value,
          },
        })
      },
    },
    system_name: {
      get() {
        return this.topic?.system_name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            system_name: value,
          },
        })
      },
    },
    activeAgentDetailId() {
      return this.$route.params.id
    },
    activeAgentDetailName() {
      return this.items?.find((item) => item.id == this.activeAgentDetailId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
    },
    loading() {
      return !this.draft?.id
    },
  },

  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    deleteAgentDetail() {
      this.$q.notify({
        message: `Are you sure you want to delete ${this.selectedRow?.name}?`,
        color: 'red-9', textColor: 'white',
        icon: 'error',
        group: 'error',
        timeout: 0,
        actions: [
          {
            label: 'Cancel',
            color: 'yellow',
            handler: () => {
              /* ... */
            },
          },
          {
            label: 'Delete',
            color: 'white',
            handler: () => {
              this.loadingDelelete = true
              this.removeMutation.mutate(this.selectedRow?.id)
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                color: 'green-9', textColor: 'white',
                icon: 'check_circle',
                group: 'success',
                message: 'Prompt has been deleted.',
                timeout: 1000,
              })
              this.navigate('/prompt-templates')
            },
          },
        ],
      })
    },
  },
}
</script>

<style lang="stylus">

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}

.breadcrumb-link {
  cursor: pointer;
}

.breadcrumb-link:hover {
  text-decoration: underline;
}
</style>
