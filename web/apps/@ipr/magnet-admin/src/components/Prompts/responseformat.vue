<template lang="pug">
div
  km-section(title='Respond with JSON', subTitle='Parameters that control the output format')
    q-chip.km-small-chip.q-mb-lg(
      v-if='!currentModelObject?.json_mode',
      flat,
      text-color='text-grey',
      :label='`Parameter is not available for selected model ${modelName}`'
    )
    .row.items-center
      .km-field.text-secondary-text.q-mr-md Respond with JSON
      q-toggle(v-model='responseWithJSON', :disable='!currentModelObject?.json_mode', dense)
    .km-field.text-secondary-text.q-my-sm Ensures that valid JSON is produced.
    template(v-if='responseWithJSON')
      km-notification-text
        .q-my-sm
          .km-chip.text-secondary-text.q-mb-sm You must instruct the model to respond with JSON in Prompt Template body.
          .km-field.text-secondary-text.q-mb-sm JSON mode alone does not guarantee the output matches a specific schema.
          .km-field.text-secondary-text Keep in mind
            |
            a.km-link.word-break-all.cursor-pointer(:href='currentModelObject?.jsonFormatDocumetaion', target='_blank') edge cases
            | that can result in the model output not being a complete JSON object.
      q-separator.q-my-lg
      q-chip.km-small-chip.q-mb-lg(
        v-if='!currentModelObject?.json_schema',
        flat,
        text-color='text-grey',
        :label='`Parameter is not available for selected model ${modelName}`'
      )
      .row.items-center
        .km-field.text-secondary-text.q-pb-xs.q-mr-lg Match schema
        q-toggle(v-model='isMatchSchema', dense, :disable='!currentModelObject?.json_schema')
      .row.q-mb-md
        .km-field.text-secondary-text.q-mt-sm Ensure that response adheres to provided schema.
      template(v-if='isMatchSchema')
        .km-field.text-secondary-text.q-pb-xs JSON schema
          km-codemirror(v-model='matchSchema')
          .km-description.text-secondary-text.q-pb-4 If filled in, output will match provided schema
</template>

<script>
export default {
  computed: {
    modelOptions() {
      return (this.$store.getters['chroma/model'].items || []).filter((el) => el.type === 'prompts')
    },
    currentModelObject() {
      return (this.modelOptions ?? []).find((el) => el.system_name === this.$store.getters.promptTemplateVariant?.system_name_for_model)
    },
    responseWithJSON: {
      get() {
        return (
          this.$store.getters.promptTemplateVariant?.response_format?.type == 'json_object' ||
          this.$store.getters.promptTemplateVariant?.response_format?.type == 'json_schema'
        )
      },
      set(value) {
        if (value) {
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.type', value: 'json_object' })
        } else {
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.type', value: 'text' })
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.json_schema', value: null })
        }
      },
    },
    isMatchSchema: {
      get() {
        return this.$store.getters.promptTemplateVariant?.response_format?.type == 'json_schema'
      },
      set(value) {
        if (value) {
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.type', value: 'json_schema' })
        } else {
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.type', value: 'json_object' })
        }
      },
    },
    schemaName: {
      get() {
        return 'NAME_' + this.$store.getters.promptTemplate?.system_name || 'NAME'
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.json_schema.name', value })
      },
    },
    modelName() {
      return this.currentModelObject?.label
    },

    matchSchema: {
      get() {
        return this.$store.getters.promptTemplateVariant?.response_format?.json_schema?.schema || ''
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', {
          path: 'response_format.json_schema',
          value: { strict: true, schema: {}, name: this.schemaName },
        })
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'response_format.json_schema.schema', value: value })
      },
    },
  },
}
</script>
