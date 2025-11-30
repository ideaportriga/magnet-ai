<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else)
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .q-my-lg
          q-breadcrumbs.text-grey(active-color='text-grey', gutter='lg')
            template(v-slot:separator)
              q-icon(size='12px', name='fas fa-chevron-right', color='text-grey')
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize Agent
                .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/agents/${$route.params?.id}`)') {{ agentName }}
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize Topic
                .km-chip.text-grey-8.text-capitalize {{ name }}

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
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { selected, selectedRow, ...useCollection } = useChroma('agents')
    return {
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
      selected,
      useCollection,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    agentName() {
      return this.$store.getters.agent_detail?.name
    },
    agentId() {
      return this.$store.getters.agent_detail?.id
    },
    name: {
      get() {
        return this.topic?.name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
      return !this.$store?.getters?.agent_detail?.id
    },
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setAgentDetail', newVal)
        this.tab = 'prompts'
      }
    },
  },
  mounted() {
    if (this.activeAgentDetailId != this.agentId) {
      this.$store.commit('setAgentDetail', this.selectedRow)
      this.tab = 'prompts'
    }
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
        color: 'error-text',
        position: 'top',
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
              this.useCollection.delete({ id: this.selectedRow?.id })
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                position: 'top',
                message: 'Prompt has been deleted.',
                color: 'positive',
                textColor: 'black',
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
