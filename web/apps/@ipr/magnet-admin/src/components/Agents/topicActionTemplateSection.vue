<template lang="pug">
div
  km-section(title='Topic processing Prompt Template', subTitle='Provides general instructions and is applicable to all Topics across Agent.')
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
import { useChroma } from '@shared'

export default {
  setup() {
    const { items: promptTemplateItems } = useChroma('promptTemplates')

    return {
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
    topicProcessingPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicProcessingPromptTemplate)?.id
    },
    topicProcessingPromptTemplate: {
      get() {
        return this.$store.getters.agentDetailVariant?.value.prompt_templates?.topic_processing
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'prompt_templates.topic_processing', value })
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
