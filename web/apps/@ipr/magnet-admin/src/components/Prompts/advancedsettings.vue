<template>
  <div>
    <km-section :title="m.section_llmModel()" :sub-title="m.subtitle_chooseModel()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_llmModel() }}</div>
      <km-select v-model="model" height="auto" min-height="36px" :placeholder="m.common_llmModel()" :options="modelOptions" option-label="display_name" option-value="system_name" emit-value has-dropdown-search>
        <template #option="{ itemProps, opt, toggleOption }">
          <li class="km-item ba-border" v-bind="itemProps" dense @click="toggleOption(opt)">
            <div class="km-item-section">
              <span class="km-item-label km-label">{{ opt.display_name }}</span>
              <div v-if="opt.provider_system_name" class="cluster mt-xs">
                <km-chip tone="brand" size="sm" dense>{{ opt.provider_system_name }}</km-chip>
              </div>
            </div>
          </li>
        </template>
      </km-select>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.prompts_outputDiversity()" :sub-title="m.subtitle_temperature()">
      <km-slider-card v-model="temperature" class="mb-lg" name="Temperature" :min="0" :max="2" :default-value="1" :min-label="m.prompts_lessRandom()" :max-label="m.prompts_moreRandom()" :description="m.prompts_recommendAltering()" :info-tooltip="m.prompts_temperatureTooltip()" />
    </km-section>
    <km-section>
      <km-slider-card v-model="topP" name="Top P" :min="0" :max="1" :default-value="1" :min-label="m.prompts_lessDiverse()" :max-label="m.prompts_moreDiverse()" :description="m.prompts_recommendAltering()" :info-tooltip="m.prompts_topPTooltip()" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_outputLimit()" :sub-title="m.subtitle_outputLimit()">
      <div class="km-field text-secondary-text pb-xs pl-sm">
        {{ m.prompts_maxTokens() }}
        <div style="max-inline-size: 200px">
          <km-input v-model="maxTokens" type="number" height="30px" :placeholder="m.prompts_maxTokens()" />
        </div>
        <div class="km-description text-secondary-text pb-xs">{{ m.prompts_tokenApprox() }}</div>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.nav_observability()" :sub-title="m.prompts_controlLogging()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.prompts_loggingLevel() }}</div>
      <km-select v-model="observabilityLevel" height="auto" min-height="36px" :placeholder="m.prompts_selectLoggingLevel()" :options="observabilityLevelOptions" option-label="label" option-value="value" emit-value map-options />
      <div class="km-description text-secondary-text pt-xs pl-sm">{{ observabilityLevelDescription }}</div>
    </km-section>
  </div>
</template>

<script>
import { isEqual } from 'lodash'
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('promptTemplates')
    const { data: modelListData } = queries.model.useList()
    const modelItems = computed(() => modelListData.value?.items ?? [])

    return {
      m,
      activeVariant,
      updateVariantField,
      modelItems,
      test: ref(true),
      iconPicker: ref(false),
      showError: ref(false),
      selectedEntity: ref(),
      promptInput: ref(null),
      llm: ref(true),
      semanticCache: ref(false),
      semanticCacheChoice: ref('faq'),
      isReRanking: ref(false),
      reRankingChoice: ref('cross'),
      reRankingCrossModel: ref(''),
      reRankingLlmModel: ref(''),
      cacheCollection: ref('Helpdesk Cache'),
      allowBypassCache: ref(false),
      observabilityLevelOptions: ref([
        { label: m.prompts_loggingFull(), value: 'full' },
        { label: m.prompts_loggingMetadataOnly(), value: 'metadata-only' },
        { label: m.prompts_loggingNone(), value: 'none' },
      ]),
    }
  },
  computed: {
    observabilityLevel: {
      get() {
        return this.activeVariant?.observability_level || 'full'
      },
      set(value) {
        this.updateVariantField('observability_level', value)
      },
    },
    observabilityLevelDescription() {
      const descriptions = {
        'full': 'Logs everything including input messages and output responses. Best for debugging and analysis.',
        'metadata-only': 'Logs only metadata like token count, cost, and latency. Input/output content is not stored.',
        'none': 'Disables all logging for this prompt template. No traces or metrics will be recorded.',
      }
      return descriptions[this.observabilityLevel] || descriptions['full']
    },
    temperature: {
      get() {
        return this.activeVariant?.temperature
      },
      set(value) {
        this.updateVariantField('temperature', value)
      },
    },
    maxTokens: {
      get() {
        return this.activeVariant?.maxTokens || null
      },
      set(value) {
        const intValue = parseInt(value, 10)

        if (!isNaN(intValue)) {
          this.updateVariantField('maxTokens', intValue)
        }
      },
    },

    topP: {
      get() {
        return this.activeVariant?.topP
      },
      set(value) {
        this.updateVariantField('topP', value)
      },
    },
    model: {
      get() {
        if (this.activeVariant?.system_name_for_model) return this.activeVariant.system_name_for_model
        return (this.modelOptions ?? []).find((el) => el.model === this.activeVariant?.model)?.system_name || ''
      },
      set(value) {
        if (!value) {
          this.updateVariantField('system_name_for_model', null)
          this.updateVariantField('model', null)
          return
        }

        const selectedModel = typeof value === 'string'
          ? (this.modelOptions ?? []).find((el) => el?.system_name === value)
          : value

        if (!selectedModel?.system_name) return

        this.updateVariantField('system_name_for_model', selectedModel.system_name)
        // Backward compat: keep old `model` field in sync until backend fully migrates to system_name_for_model
        if (selectedModel.model) this.updateVariantField('model', selectedModel.model)
      }
    },
    modelOptions() {
      return (this.modelItems || [])
        .filter((el) => el.type === 'prompts')
        .sort((a, b) => a.display_name.localeCompare(b.display_name))
    },

    hasChanges() {
      if (this.selectedRow?.id !== undefined) return !isEqual(this.prompt, this.selectedRow)
      else return true
    },
    hasError() {
      return !(this.prompt.name && this.prompt.text && this.prompt.description)
    },
    isNew() {
      return this.prompt && this.prompt.id === undefined
    },
    canSave() {
      return !!this.prompt.text && !!this.prompt.description && !!this.prompt.name
    },
  },
  created() {},
  methods: {
    setProp(name, val) {
      this.$emit('setProp', { name, val })
    },
    save() {
      if (this.hasError) {
        this.showError = true
        return
      }
      this.showError = false
      this.$emit('save')
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
