<template lang="pug">
div
  km-section(:title='m.section_respondWithJson()', :subTitle='m.subtitle_outputFormat()')
    q-chip.km-small-chip.q-mb-lg(
      v-if='!currentModelObject?.json_mode',
      flat,
      text-color='text-grey',
      :label='m.prompts_paramNotAvailable({ model: modelName })'
    )
    .row.items-center
      .km-field.text-secondary-text.q-mr-md {{ m.section_respondWithJson() }}
      q-toggle(v-model='responseWithJSON', :disable='!currentModelObject?.json_mode', dense)
    .km-field.text-secondary-text.q-my-sm {{ m.prompts_ensuresValidJson() }}
    template(v-if='responseWithJSON')
      km-notification-text
        .q-my-sm
          .km-chip.text-secondary-text.q-mb-sm {{ m.prompts_mustInstructJson() }}
          .km-field.text-secondary-text.q-mb-sm {{ m.prompts_jsonNoGuarantee() }}
          .km-field.text-secondary-text {{ m.prompts_keepInMind() }}
            |
            a.km-link.word-break-all.cursor-pointer(:href='currentModelObject?.jsonFormatDocumetaion', target='_blank') edge cases
            |  {{ m.prompts_edgeCasesResult() }}
      q-separator.q-my-lg
      q-chip.km-small-chip.q-mb-lg(
        v-if='!currentModelObject?.json_schema',
        flat,
        text-color='text-grey',
        :label='m.prompts_paramNotAvailable({ model: modelName })'
      )
      .row.items-center
        .km-field.text-secondary-text.q-pb-xs.q-mr-lg {{ m.prompts_matchSchema() }}
        q-toggle(v-model='isMatchSchema', dense, :disable='!currentModelObject?.json_schema')
      .row.q-mb-md
        .km-field.text-secondary-text.q-mt-sm {{ m.prompts_ensureResponseSchema() }}
      template(v-if='isMatchSchema')
        .km-field.text-secondary-text.q-pb-xs JSON schema
          km-codemirror(v-model='matchSchema')
          .km-description.text-secondary-text.q-pb-4 If filled in, output will match provided schema
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  setup() {
    const queries = useEntityQueries()
    const { draft, activeVariant, updateVariantField } = useVariantEntityDetail('promptTemplates')
    const { data: modelListData } = queries.model.useList()
    const modelItems = computed(() => modelListData.value?.items ?? [])

    return {
      draft,
      activeVariant,
      updateVariantField,
      modelItems,
    }
  },
  computed: {
    modelOptions() {
      return (this.modelItems || []).filter((el) => el.type === 'prompts')
    },
    currentModelObject() {
      return (this.modelOptions ?? []).find((el) => el.system_name === this.activeVariant?.system_name_for_model)
    },
    responseWithJSON: {
      get() {
        return (
          this.activeVariant?.response_format?.type == 'json_object' ||
          this.activeVariant?.response_format?.type == 'json_schema'
        )
      },
      set(value) {
        if (value) {
          this.updateVariantField('response_format.type', 'json_object')
        } else {
          this.updateVariantField('response_format.type', 'text')
          this.updateVariantField('response_format.json_schema', null)
        }
      },
    },
    isMatchSchema: {
      get() {
        return this.activeVariant?.response_format?.type == 'json_schema'
      },
      set(value) {
        if (value) {
          this.updateVariantField('response_format.type', 'json_schema')
        } else {
          this.updateVariantField('response_format.type', 'json_object')
        }
      },
    },
    schemaName: {
      get() {
        return 'NAME_' + this.draft?.system_name || 'NAME'
      },
      set(value) {
        this.updateVariantField('response_format.json_schema.name', value)
      },
    },
    modelName() {
      return this.currentModelObject?.label
    },

    matchSchema: {
      get() {
        return this.activeVariant?.response_format?.json_schema?.schema || ''
      },
      set(value) {
        this.updateVariantField('response_format.json_schema', { strict: true, schema: {}, name: this.schemaName })
        this.updateVariantField('response_format.json_schema.schema', value)
      },
    },
  },
}
</script>
