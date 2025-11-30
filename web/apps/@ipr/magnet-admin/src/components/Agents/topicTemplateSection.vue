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
    topicSelectionPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicSelectionPromptTemplate)?.id
    },
    topicSelectionPromptTemplate: {
      get() {
        return this.$store.getters.agentDetailVariant?.value.prompt_templates?.classification
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'prompt_templates.classification', value })
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
