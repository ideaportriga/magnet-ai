<template>
  <div>
    <km-section :title="m.section_respondWithJson()" :sub-title="m.subtitle_outputFormat()">
      <km-chip v-if="!currentModelObject?.json_mode" class="km-small-chip mb-lg" flat tone="neutral" :label="m.prompts_paramNotAvailable({ model: modelName })" />
      <div class="cluster">
        <div class="km-field text-secondary-text mr-md">{{ m.section_respondWithJson() }}</div>
        <km-toggle v-model="responseWithJSON" :disable="!currentModelObject?.json_mode" dense />
      </div>
      <div class="km-field text-secondary-text my-sm">{{ m.prompts_ensuresValidJson() }}</div>
      <template v-if="responseWithJSON">
        <km-notification-text>
          <div class="my-sm">
            <div class="km-chip text-secondary-text mb-sm">{{ m.prompts_mustInstructJson() }}</div>
            <div class="km-field text-secondary-text mb-sm">{{ m.prompts_jsonNoGuarantee() }}</div>
            <div class="km-field text-secondary-text">
              {{ m.prompts_keepInMind() }}<a class="km-link word-break-all cursor-pointer" :href="currentModelObject?.jsonFormatDocumetaion" target="_blank">{{ m.prompts_edgeCases() }}</a> {{ m.prompts_edgeCasesResult() }}
            </div>
          </div>
        </km-notification-text>
        <km-separator class="my-lg" />
        <km-chip v-if="!currentModelObject?.json_schema" class="km-small-chip mb-lg" flat tone="neutral" :label="m.prompts_paramNotAvailable({ model: modelName })" />
        <div class="cluster">
          <div class="km-field text-secondary-text pb-xs mr-lg">{{ m.prompts_matchSchema() }}</div>
          <km-toggle v-model="isMatchSchema" dense :disable="!currentModelObject?.json_schema" />
        </div>
        <div class="cluster mb-md">
          <div class="km-field text-secondary-text mt-sm">{{ m.prompts_ensureResponseSchema() }}</div>
        </div>
        <template v-if="isMatchSchema">
          <div class="km-field text-secondary-text pb-xs">
            {{ m.common_jsonSchema() }}
            <km-codemirror v-model="matchSchema" />
            <div class="km-description text-secondary-text pb-xs">{{ m.prompts_outputMatchSchema() }}</div>
          </div>
        </template>
      </template>
    </km-section>
  </div>
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
      m,
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
