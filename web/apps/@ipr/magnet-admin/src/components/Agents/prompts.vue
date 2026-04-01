<template lang="pug">
div
  km-section(
    title='Topic selection Prompt Template',
    subTitle='Topic selection prompt instructs the Agent how to detect correct Topics from user input and handle cases when a Topic was not found.'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
    km-select(
      height='30px',
      placeholder='Standart Q&A Prompt',
      :options='promptTemplatesOptions',
      v-model='topicSelectionPromptTemplate',
      hasDropdownSearch,
      emit-value,
      map-options,
      option-value='system_name',
      :option-show='(item) => item?.category === "agent"'
    )
    .km-description.text-secondary-text.q-pb-4 Your Prompt Template model must support JSON mode
    .row.q-mt-sm
      .col-auto
        km-btn(
          flat,
          simple,
          :label='topicSelectionPromptTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
          iconSize='16px',
          icon='fas fa-comment-dots',
          @click='topicSelectionPromptTemplate ? navigate(`prompt-templates/${topicSelectionPromptTemplateId}`) : navigate("prompt-templates")'
        )
  q-separator.q-my-lg
  km-section(
    title='Topic processing Prompt Template',
    subTitle='Topic processing prompt provides general instructions applicable to all Topics, like tone, or general contextual information like current date.'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
    km-select(
      height='30px',
      :options='promptTemplatesOptions',
      v-model='topicProcessingPromptTemplate',
      hasDropdownSearch,
      emit-value,
      map-options,
      option-value='system_name',
      :option-show='(item) => item?.category === "agent"'
    )
    .km-description.text-secondary-text.q-pb-4 Your Prompt Template model must support tool calling
    .row.q-mt-sm
      .col-auto
        km-btn(
          flat,
          simple,
          :label='topicProcessingPromptTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
          iconSize='16px',
          icon='fas fa-comment-dots',
          @click='topicProcessingPromptTemplate ? navigate(`prompt-templates/${topicProcessingPromptTemplateId}`) : navigate("prompt-templates")'
        )
</template>

<script>
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useAgentDetailStore } from '@/stores/agentDetailStore'

export default {
  emits: ['openTest'],
  setup() {
    const queries = useEntityQueries()
    const { data: promptTemplateData } = queries.promptTemplates.useList()
    const promptTemplateItems = computed(() => promptTemplateData.value?.items ?? [])
    const agentStore = useAgentDetailStore()

    return {
      agentStore,
      promptTemplateItems,
    }
  },
  computed: {
    promptTemplatesOptions() {
      return (this.promptTemplateItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item.category,
        id: item.id,
      }))
    },
    topicSelectionPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicSelectionPromptTemplate)?.id
    },

    topicProcessingPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicProcessingPromptTemplate)?.id
    },

    topicSelectionPromptTemplate: {
      get() {
        return this.agentStore.activeVariant?.value.prompt_templates?.classification
      },
      set(value) {
        this.agentStore.updateNestedVariantProperty({ path: 'prompt_templates.classification', value })
      },
    },
    topicProcessingPromptTemplate: {
      get() {
        return this.agentStore.activeVariant?.value.prompt_templates?.topic_processing
      },
      set(value) {
        this.agentStore.updateNestedVariantProperty({ path: 'prompt_templates.topic_processing', value })
      },
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
