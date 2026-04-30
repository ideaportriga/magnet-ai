<template>
  <div class="pr-md">
    <km-section :title="m.collections_sourceSettings()" :sub-title="m.collections_sourceSettingsSubtitle()">
      <div class="flex-1 pt-sm">
        <div class="km-input-label pb-xs pl-sm">{{ m.collections_sourceType() }}</div>
        <km-select ref="source_typeRef" v-model="source_type" :options="dynamicSourceTypeOptions" :rules="config.source_type.rules" :disabled="isDisable" />
      </div>
      <template v-for="item in dynamicSourceTypeChildren[source_type]" :key="item">
        <div class="flex-1 pt-sm">
          <div class="km-input-label pb-xs pl-sm">
            {{ item.label }}
            <div v-if="item?.description" class="km-description text-secondary-text">{{ item?.description }}</div>
          </div>
          <component :is="item.component" v-model="source_fields[item.field]" :readonly="isDisable" :disable="isDisable" />
        </div>
      </template>
    </km-section><!-- CHUNKING -->
    <km-separator class="my-lg" />
    <km-section :title="m.section_chunking()" :sub-title="m.collections_chunkingSubtitle()">
      <div class="stack" data-gap="lg">
        <div class="flex-1">
          <div class="km-input-label pb-xs">{{ m.collections_chunkingStrategy() }}</div>
          <km-select v-model="chunkingStrategy" :options="config.chunking_strategy.options" emit-value map-options option-value="value" option-label="label" :disabled="isDisable" />
          <div class="km-description text-secondary-text mt-xs ml-xs">{{ m.collections_chunkingStrategyHint() }}</div>
        </div>
        <div v-if="chunkingStrategy === &quot;recursive_character_text_splitting&quot;" class="cluster" data-gap="lg">
          <div class="flex-1">
            <div class="km-input-label pb-xs">{{ m.collections_chunkSize() }}</div>
            <km-input v-model="chunkSize" type="number" :readonly="isDisable" />
            <div class="km-description text-secondary-text mt-xs ml-xs">{{ m.collections_chunkSizeHint() }}</div>
          </div>
          <div class="flex-1">
            <div class="km-input-label pb-xs">{{ m.collections_chunkOverlap() }}</div>
            <km-input v-model="chunkOverlap" type="number" :readonly="isDisable" />
            <div class="km-description text-secondary-text mt-xs ml-xs">{{ m.collections_chunkOverlapHint() }}</div>
          </div>
        </div>
        <div class="flex-1 mt-sm">
          <div class="cluster" data-align="baseline">
            <div class="flex-none mr-sm">
              <km-toggle v-model="chunkTransformationEnabled" dense :disable="isDisable" />
            </div>
            <div class="flex-1">{{ m.collections_enableChunkLlmTransformation() }}</div>
          </div>
        </div>
        <div v-if="chunkTransformationEnabled" class="stack" data-gap="lg">
          <div class="flex-1">
            <km-select v-model="chunkTransformationPromptTemplate" :options="chunkTransformationPromptTemplateOptions" has-dropdown-search emit-value map-options option-value="system_name" :disabled="isDisable" />
            <div class="km-description text-secondary-text mt-xs ml-xs">{{ m.collections_chunkTransformationPromptHint() }}</div>
            <div class="cluster mt-sm">
              <div class="flex-none">
                <km-btn :label="chunkTransformationPromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="chunkTransformationPromptTemplate ? navigate(`prompt-templates/${chunkTransformationPromptTemplateId}`) : navigate(&quot;prompt-templates&quot;)" />
              </div>
            </div>
          </div>
          <div class="flex-1">
            <div class="km-input-label pb-xs">{{ m.collections_howToApplyTransformation() }}</div>
            <km-select v-model="chunkTransformationMethod" :options="config.chunk_transformation_method.options" emit-value map-options option-value="value" option-label="label" :disabled="isDisable" />
            <div class="km-description text-secondary-text mt-xs ml-xs">{{ m.collections_howToApplyTransformationHint() }}</div>
          </div>
          <div class="flex-1">
            <div class="km-input-label pb-xs">{{ m.collections_howToUseChunks() }}</div>
            <km-select v-model="chunkUsageMethod" :options="config.chunk_usage_method.options" emit-value map-options option-value="value" option-label="label" :disabled="isDisable" />
            <div class="km-description text-secondary-text mt-xs ml-xs">{{ m.collections_howToUseChunksHint() }}</div>
          </div>
        </div>
      </div>
    </km-section><!-- INDEXING -->
    <km-separator class="my-lg" />
    <km-section :title="m.section_indexing()" :sub-title="m.collections_indexingSubtitle()">
      <div class="stack" data-gap="lg">
        <div class="km-description mt-sm">{{ m.collections_hybridSearchHint() }}</div>
        <div class="flex-1">
          <div class="cluster" data-align="baseline">
            <div class="flex-none mr-sm">
              <km-toggle v-model="supportSemanticSearch" dense :disable="true" />
            </div>
            <div class="flex-1">{{ m.collections_supportSemanticSearch() }}</div>
          </div>
          <div class="km-description text-secondary-text mt-sm">{{ m.collections_semanticSearchHint() }}</div>
        </div>
        <div v-if="supportSemanticSearch" class="flex-1">
          <div class="km-input-label pb-xs">{{ m.collections_embeddingModel() }}</div>
          <km-select v-model="embeddingModel" :placeholder="m.collections_embeddingModel()" :options="embeddingModelOptions" option-value="system_name" option-label="display_name" emit-value map-options :disabled="isDisable">
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
        </div>
        <div class="flex-1 mt-sm">
          <div class="cluster" data-align="baseline">
            <div class="flex-none mr-sm">
              <km-toggle v-model="supportKeywordSearch" dense />
            </div>
            <div class="flex-1">{{ m.collections_supportKeywordSearch() }}</div>
          </div>
          <div class="km-description text-secondary-text mt-sm">{{ m.collections_keywordSearchHint() }}</div>
        </div>
      </div>
    </km-section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { sourceTypeOptions, sourceTypeChildren } from '@/config/collections/collections'
import FileUrlUpload from '@/components/Collections/FileUrlUpload.vue'

const router = useRouter()
const route = useRoute()
const { config } = useEntityConfig('collections')
const queries = useEntityQueries()
const { draft, updateField } = useEntityDetail('collections')
const { data: promptTemplateListData } = queries.promptTemplates.useList()
const { data: modelListData } = queries.model.useList()

// Dynamic source type options from loaded plugins
const dynamicSourceTypeOptions = computed(() => sourceTypeOptions.value || [])
const dynamicSourceTypeChildren = computed(() => sourceTypeChildren.value || {})

const isDisable = computed(() => {
  if (!draft.value?.last_synced) return false
  const d = new Date(draft.value.last_synced)
  return !isNaN(d.getTime())
})

const source_fields = computed({
  get() {
    const source = draft.value?.source || {}

    // Transform Documentation arrays to comma-separated strings for display
    if (source.source_type === 'Documentation') {
      const transformed = { ...source }

      // Convert languages array to string
      if (Array.isArray(transformed.languages)) {
        transformed.languages = transformed.languages.join(', ')
      }

      // Convert sections array to string
      if (Array.isArray(transformed.sections)) {
        transformed.sections = transformed.sections.join(', ')
      }

      return transformed
    }

    return source
  },
  set(value) {
    updateField('source', value)
  },
})

const source_type = computed({
  get() { return draft.value?.source?.source_type || '' },
  set(value) { updateField('source', { ...(draft.value?.source || {}), source_type: value }) },
})

// Chunking settings
const chunkingStrategy = computed({
  get() { return draft.value?.chunking?.strategy || 'recursive_character_text_splitting' },
  set(value) { updateField('chunking.strategy', value) },
})
const chunkSize = computed({
  get() {
    const val = draft.value?.chunking?.chunk_size
    return val != null ? String(val) : ''
  },
  set(value) { updateField('chunking.chunk_size', parseInt(value)) },
})
const chunkOverlap = computed({
  get() {
    const val = draft.value?.chunking?.chunk_overlap
    return val != null ? String(val) : ''
  },
  set(value) { updateField('chunking.chunk_overlap', parseInt(value)) },
})
const chunkTransformationEnabled = computed({
  get() { return draft.value?.chunking?.transformation_enabled || false },
  set(value) { updateField('chunking.transformation_enabled', value) },
})
const chunkTransformationPromptTemplate = computed({
  get() { return draft.value?.chunking?.transformation_prompt_template || '' },
  set(value) { updateField('chunking.transformation_prompt_template', value) },
})
const chunkTransformationMethod = computed({
  get() { return draft.value?.chunking?.transformation_method || '' },
  set(value) { updateField('chunking.transformation_method', value) },
})
const chunkUsageMethod = computed({
  get() { return draft.value?.chunking?.chunk_usage_method || '' },
  set(value) { updateField('chunking.chunk_usage_method', value) },
})

const promptTemplateItems = computed(() => promptTemplateListData.value?.items ?? [])
const chunkTransformationPromptTemplateOptions = computed(() =>
  (promptTemplateItems.value ?? []).map((item) => ({
    label: item.name,
    value: item.id,
    system_name: item.system_name,
    category: item?.category,
    id: item.id,
  }))
)
const chunkTransformationPromptTemplateId = computed(() =>
  chunkTransformationPromptTemplateOptions.value.find((el) => el.system_name == chunkTransformationPromptTemplate.value)?.id
)

// Indexing settings
const supportSemanticSearch = computed({
  get() {
    if (!draft.value?.indexing) return true
    return draft.value?.indexing?.semantic_search_supported || false
  },
  set(value) { updateField('indexing.semantic_search_supported', value) },
})
const embeddingModel = computed({
  get() { return draft.value?.ai_model || '' },
  set(value) { updateField('ai_model', value) },
})
const embeddingModelOptions = computed(() =>
  (modelListData.value?.items ?? []).filter((el) => el.type === 'embeddings')
)
const supportKeywordSearch = computed({
  get() { return draft.value?.indexing?.fulltext_search_supported || false },
  set(value) { updateField('indexing.fulltext_search_supported', value) },
})

function navigate(path = '') {
  if (route.path !== `/${path}`) {
    router.push(`/${path}`)
  }
}
</script>
