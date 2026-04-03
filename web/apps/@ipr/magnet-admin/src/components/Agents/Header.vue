<template lang="pug">
.col-auto.q-py-auto.row.items-center.no-wrap.q-gap-8
  template(v-if='activeActionId')
    .km-body.text-primary.km-breadcrumb-link(@click='navigate(`/agents/${activeRowId}`)') {{ activeRowName }}
    q-icon.text-secondary-text.km-breadcrumb-sep(name='chevron_right', size='18px')
    .km-body.text-primary.km-breadcrumb-link(@click='navigate(`/agents/${activeRowId}/topics/${activeTopicId}`)') {{ activeTopic?.name || m.entity_topic() }}
    q-icon.text-secondary-text.km-breadcrumb-sep(name='chevron_right', size='18px')
    .km-body {{ activeAction?.name || m.entity_action() }}
  template(v-else-if='activeTopicId')
    .km-body.text-primary.km-breadcrumb-link(@click='navigate(`/agents/${activeRowId}`)') {{ activeRowName }}
    q-icon.text-secondary-text.km-breadcrumb-sep(name='chevron_right', size='18px')
    .km-body {{ activeTopic?.name || m.entity_topic() }}
  template(v-else)
    .km-body {{ activeRowName }}
</template>

<script>
import { computed } from 'vue'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { m } from '@/paraglide/messages'

export default {
  props: ['activeRow'],
  setup() {
    useAgentEntityDetail()
    const { options: items } = useCatalogOptions('agents')

    return {
      m,
      items,
    }
  },
  computed: {
    activeRowId() {
      return this.$route.params.id
    },
    activeTopicId() {
      return this.$route.params?.topicId || ''
    },
    activeActionId() {
      return this.$route.params?.actionId || ''
    },
    activeAgent() {
      return this.items.find((item) => item.id == this.activeRowId)
    },
    activeTopic: {
      get() {
        return this.activeAgent?.variants
          ?.find((el) => this.activeAgent.active_variant === el?.variant)
          ?.value?.topics?.find((el) => el.system_name == this.activeTopicId)
      },
    },
    activeAction() {
      return this.activeTopic?.actions?.find((el) => el.system_name == this.activeActionId)
    },
    activeRowDB() {
      return this.activeAgent
    },
    activeRowName: {
      get() {
        return this.activeRowDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
  },
}
</script>
