<template>
  <km-dialog :model-value="showNewDialog" @hide="onDialogHide">
    <km-card class="card-style px-md" style="min-inline-size: 800px">
      <div class="km-card-section card-section-style mb-md">
        <div class="cluster" data-justify="between">
          <div class="km-heading-7">{{ m.dialog_newKnowledgeSource() }}</div>
          <km-btn icon="close" flat dense @click="$emit(&quot;cancel&quot;)" />
        </div>
      </div>
      <div class="km-card-section card-section-style mb-md">
        <div class="cluster" data-justify="center">
          <km-stepper class="full-width" :steps="[ { step: 0, description: m.collections_basicConfiguration(), icon: &quot;pen&quot; }, { step: 1, description: m.collections_chunkingSettings(), icon: &quot;circle&quot; }, { step: 2, description: m.collections_indexingSettings(), icon: &quot;circle&quot; }, { step: 3, description: m.collections_schedule(), icon: &quot;schedule&quot; }, ]" :stepper="stepper" />
        </div>
        <div v-if="stepper === 0" class="stack full-width">
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
          <div class="full-width mb-md">
            <km-input ref="nameRef" v-model="nameCalc" data-test="name-input" :rules="config.name.rules" />
          </div>
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_systemName() }}</div>
          <div class="full-width mb-md">
            <km-input ref="system_nameRef" v-model="system_name" data-test="system-name-input" :rules="config.system_name.rules" />
          </div>
          <template v-for="item in dynamicSourceTypeChildren[source_type]" :key="item">
            <div class="flex-1">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ item.label }}</div>
              <div class="mb-md">
                <component :is="item.component" ref="sourceComponents" v-model="source[item.field]" />
              </div>
            </div>
          </template>
        </div>
        <div v-if="stepper === 1" class="stack full-width">
          <div class="flex-1 pt-sm mt-sm">
            <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.collections_chunkingStrategy() }}</div>
            <km-select ref="chunking_strategyRef" v-model="chunkingStrategy" :placeholder="m.collections_chunkingStrategy()" :options="config.chunking_strategy.options" :rules="config.chunking_strategy.rules" emit-value map-options option-value="value" option-label="label" />
            <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_chunkingStrategyHint() }}</div>
          </div>
          <div v-if="chunkingStrategy === &quot;recursive_character_text_splitting&quot;" class="cluster" data-gap="lg">
            <div class="flex-1 pt-sm mt-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.collections_chunkSize() }}</div>
              <km-input ref="maxChunkRef" v-model="chunkSize" type="number" />
              <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_chunkSizeHint() }}</div>
            </div>
            <div class="flex-1 pt-sm mt-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.collections_chunkOverlap() }}</div>
              <km-input ref="maxChunkRef" v-model="chunkOverlap" type="number" />
              <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_chunkOverlapHint() }}</div>
            </div>
          </div>
          <div class="flex-1 pt-sm mt-md pl-sm">
            <div class="cluster" data-align="baseline">
              <div class="flex-none mr-sm">
                <div class="km-field text-secondary-text absolute ml-4xl">{{ m.collections_enableChunkLlmTransformation() }}</div>
                <km-toggle v-model="chunkTransformationEnabled" dense />
              </div>
            </div>
          </div>
          <div v-if="chunkTransformationEnabled" class="stack" data-gap="lg" style="padding-block-start: 2px; margin-block-start: var(--ds-space-sm)">
            <div v-if="chunkTransformationEnabled" class="flex-1">
              <km-select v-model="chunkTransformationPromptTemplate" :placeholder="m.collections_selectPromptTemplate()" :options="chunkTransformationPromptTemplateOptions" has-dropdown-search emit-value map-options option-value="system_name" />
              <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_chunkTransformationPromptHint() }}</div>
            </div>
            <div class="flex-1">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.collections_howToApplyTransformation() }}</div>
              <km-select v-model="chunkTransformationMethod" :options="config.chunk_transformation_method.options" :placeholder="m.collections_selectHowToApplyTransformation()" emit-value map-options option-value="value" option-label="label" :disabled="isDisable" />
              <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_howToApplyTransformationHint() }}</div>
            </div>
            <div class="flex-1">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.collections_howToUseChunks() }}</div>
              <km-select v-model="chunkUsageMethod" :options="config.chunk_usage_method.options" :placeholder="m.collections_selectHowToUseChunks()" emit-value map-options option-value="value" option-label="label" :disabled="isDisable" />
              <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_howToUseChunksHint() }}</div>
            </div>
          </div>
        </div>
        <div v-if="stepper === 2" class="stack full-width">
          <div class="km-description mt-sm pl-sm">{{ m.collections_hybridSearchHint() }}</div>
          <div class="flex-1 pt-sm mt-md pl-sm">
            <div class="cluster" data-align="baseline">
              <div class="flex-none mr-sm">
                <div class="km-field text-secondary-text absolute ml-4xl">{{ m.collections_supportSemanticSearch() }}</div>
                <km-toggle ref="semantic_search_supportedRef" v-model="supportSemanticSearch" :rules="[indexingRules()]" dense :disable="true" />
              </div>
            </div>
          </div>
          <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_semanticSearchHint() }}</div>
          <div v-if="supportSemanticSearch" class="flex-1 pt-sm mt-sm">
            <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.collections_embeddingModel() }}</div>
            <km-select v-model="ai_model" height="auto" min-height="36px" :placeholder="m.collections_embeddingModel()" :options="modelOptions" option-label="display_name" emit-value map-options option-value="system_name">
              <template #option="{ itemProps, opt, toggleOption }">
                <li class="km-item ba-border" v-bind="itemProps" dense @click="toggleOption(opt)">
                  <div class="km-item-section">
                    <span class="km-item-label km-label">{{ opt.display_name }}</span>
                    <div v-if="opt.provider_system_name" class="mt-xs">
                      <km-chip tone="brand" size="sm" dense>{{ opt.provider_system_name }}</km-chip>
                    </div>
                  </div>
                </li>
              </template>
            </km-select>
          </div>
          <div class="flex-1 pt-sm mt-md pl-sm">
            <div class="cluster" data-align="baseline">
              <div class="flex-none mr-sm">
                <div class="km-field text-secondary-text absolute ml-4xl">{{ m.collections_supportKeywordSearch() }}</div>
                <km-toggle ref="support_keyword_searchRef" v-model="supportKeywordSearch" :rules="[indexingRules()]" dense />
              </div>
            </div>
          </div>
          <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.collections_keywordSearchHint() }}</div>
        </div>
        <div v-if="stepper === 3" class="stack full-width">
          <div class="km-button-xs-text text-secondary-text">
            {{ m.collections_scheduleSync() }}
            <km-toggle ref="scheduleEnabledRef" v-model="scheduleEnabled" height="30px" />
            <div class="km-description text-secondary-text">{{ m.collections_automaticallySyncKnowledgeSource() }}</div>
            <template v-if="scheduleEnabled">
              <div class="px-md mt-md">
                <div class="km-field text-secondary-text pb-xs pl-sm pt-md">{{ m.collections_jobInterval() }}</div>
                <div class="full-width">
                  <km-btn-toggle v-model="form.interval" :options="intervals" dense />
                </div>
                <div v-if="form.interval === &quot;daily&quot; || form.interval === &quot;weekly&quot;" class="cluster mt-md pl-sm" data-gap="sm">
                  <div v-if="form.interval === &quot;weekly&quot;" class="cluster" data-gap="sm">
                    <div class="km-field text-secondary-text">{{ m.collections_every() }}</div>
                    <km-select v-model="form.day" :options="days" />
                  </div>
                  <div class="cluster" data-gap="sm">
                    <div class="km-field text-secondary-text">{{ m.collections_at() }}</div>
                    <km-select v-model="form.time" :options="times" />
                  </div>
                </div>
                <div v-if="form.interval === &quot;custom&quot;" class="mt-md pl-sm">
                  <div class="km-field text-secondary-text pb-xs">{{ m.collections_cronExpression() }}</div>
                  <km-input v-model="form.customCron" height="30px" :placeholder="m.common_cronExpression()" />
                  <div class="km-tiny text-secondary-text mt-xs">{{ m.collections_cronFormatHint() }}</div>
                </div>
                <div class="cluster mt-md" data-gap="sm">
                  <km-checkbox v-model="form.enabled" size="40px" />
                  <div class="km-field">{{ m.collections_sendErrorNotifications() }}</div>
                </div>
                <div class="km-tiny text-secondary-text">{{ m.collections_errorNotificationHint() }}</div>
                <template v-if="form.enabled">
                  <div class="km-field text-secondary-text pb-xs pl-sm pt-md">{{ m.collections_errorNotificationEmail() }}</div>
                  <div class="full-width">
                    <km-input ref="errorEmailRef" v-model="form.error_email" height="30px" />
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>
        <div class="cluster mt-lg" data-justify="between">
          <km-btn data-test="cancel-btn" flat :label="m.common_cancel()" tone="brand" @click="cancelCreate" />
          <div class="cluster" data-gap="lg" data-wrap="no">
            <template v-if="stepper === 0">
              <km-btn data-test="next-btn" :label="m.common_next()" @click="next(1)" />
            </template>
            <template v-else-if="stepper === 1">
              <km-btn data-test="back-btn" flat :label="m.common_back()" @click="stepper = 0" />
              <km-btn data-test="next-btn" :label="m.common_next()" @click="next(2)" />
            </template>
            <template v-else-if="stepper === 2">
              <km-btn data-test="back-btn" flat :label="m.common_back()" @click="stepper = 1" />
              <km-btn data-test="next-btn" :label="m.common_next()" @click="next(3)" />
            </template>
            <template v-else-if="stepper === 3">
              <km-btn data-test="back-btn" flat :label="m.common_back()" :disable="loadingCreate" @click="stepper = 2" />
              <km-btn data-test="save-btn" :label="m.common_save()" :disable="loadingCreate" @click="createNew(false)" />
              <km-btn data-test="save-and-sync-btn" :label="m.common_saveAndSync()" :disable="loadingCreate" @click="createNew(true)" />
            </template>
          </div>
        </div>
      </div>
      <km-inner-loading :showing="loadingCreate" size="50px" />
    </km-card>
  </km-dialog>
</template>
<script>
import { defineComponent, ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@/utils/validationRules'
import { toUpperCaseWithUnderscores, fetchData } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'
import { useEntityQueries } from '@/queries/entities'
import { sourceTypeOptions, sourceTypeChildren } from '@/config/collections/collections'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
import { useCollectionDetailStore } from '@/stores/entityDetailStores'
import FileUrlUpload from '@/components/Collections/FileUrlUpload.vue'
import { notify } from '@shared/utils/notify'

export default defineComponent({
  components: {
    'collections-file-url-upload': FileUrlUpload,
    'file-url-upload': FileUrlUpload,
  },
  props: {
    showNewDialog: Boolean,
    copy: Boolean,
    providerSystemName: {
      type: String,
      default: null,
    },
  },
  emits: ['cancel'],
  setup(props) {
    const { config, requiredFields } = useEntityConfig('collections')
    const queries = useEntityQueries()
    const { draft: existingDraft } = useEntityDetail('collections')
    const tempEntity = ref(null)
    const { data: promptTemplateListData } = queries.promptTemplates.useList()
    const { data: providerListData } = queries.provider.useList()
    const { mutateAsync: createCollection } = queries.collections.useCreate()
    const { mutateAsync: updateCollection } = queries.collections.useUpdate()
    const { data: modelListData } = queries.model.useList()

    const intervals = [
      { label: 'Every 5 min', value: 'every_5_minutes' },
      { label: 'Hourly', value: 'hourly' },
      { label: 'Daily', value: 'daily' },
      { label: 'Weekly', value: 'weekly' },
      { label: 'Custom', value: 'custom' },
    ]
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    const times = Array.from({ length: 24 }, (_, i) => ({ label: `${i.toString().padStart(2, '0')}:00`, value: i.toString().padStart(2, '0') }))

    return {
      m,
      customFields: ref({}),
      metadata: ref('{}'),
      show_in_qa: ref(false),
      category: ref(''),
      type: ref(''),
      name: ref(''),
      system_name: ref(''),
      description: ref(''),
      source: ref({}),
      provider_system_name: ref(''),

      // Chunking settings
      chunkingStrategy: ref('recursive_character_text_splitting'),
      chunkSize: ref(12000),
      chunkOverlap: ref(2000),
      chunkTransformationEnabled: ref(false),
      chunkTransformationPromptTemplate: ref(''),
      chunkTransformationMethod: ref('replace'),
      chunkUsageMethod: ref('transformed_indexing_original_retrieval'),

      // Indexing settings
      supportSemanticSearch: ref(true),
      ai_model: ref(''),
      supportFullTextSearch: ref(false),
      supportKeywordSearch: ref(false),

      loadingCreate: ref(false),
      jsonError: ref(false),
      required,
      minLength,
      // required_fields: ['name', 'title', 'source_type' ,'category','type'],
      requiredFields,
      config,
      createCollection,
      updateCollection,
      promptTemplateListData,
      providerListData,
      modelListData,
      autoChangeCode: ref(true),
      isMounted: ref(false),
      stepper: ref(0),
      scheduleEnabled: ref(false),
      days,
      intervals,
      times,
      form: reactive({
        name: '',
        interval: 'hourly',
        day: 'Monday',
        time: '00:00',
        enabled: true,
        error_email: '',
        customCron: '*/10 * * * *',
      }),
      // Direct access to reactive plugin data
      sourceTypeOptions,
      sourceTypeChildren,
      tempEntity,
      existingDraft,
      collectionDetailStore: useCollectionDetailStore(),
      appStore: useAppStore(),
      // New reactive property for sync confirmation display
    }
  },
  computed: {
    promptTemplateItems() {
      return this.promptTemplateListData?.items ?? []
    },
    providerItems() {
      return this.providerListData?.items ?? []
    },
    providerOptions() {
      // Filter only knowledge providers
      return (this.providerItems || []).filter((provider) => provider.category === 'knowledge')
    },
    selectedProvider() {
      if (!this.provider_system_name) return null
      return this.providerItems?.find((p) => p.system_name === this.provider_system_name)
    },
    source_type: {
      get() {
        return this.source?.source_type || ''
      },
      set(val) {
        this.source = { ...this.source, source_type: val }
      },
    },

    // Dynamic source type options from loaded plugins
    dynamicSourceTypeOptions() {
      if (this.selectedProvider) {
        // If provider is selected, only show the source type matching the provider's type
        return this.sourceTypeOptions.filter((option) => option.value === this.selectedProvider.type) || []
      }
      return this.sourceTypeOptions || []
    },

    // Dynamic source type children from loaded plugins
    dynamicSourceTypeChildren() {
      return this.sourceTypeChildren || {}
    },

    defaultModel() {
      return this.modelOptions?.find((el) => el.is_default)?.system_name
    },
    chunkTransformationPromptTemplateOptions() {
      return (this.promptTemplateItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item?.category,
        id: item.id,
      }))
    },
    modelItems() {
      return this.modelListData?.items ?? []
    },
    modelOptions() {
      return (this.modelItems || []).filter((el) => el.type === 'embeddings')
    },
    currentRaw() {
      return this.tempEntity || this.existingDraft
    },
    nameCalc: {
      get() {
        return this.name || ''
      },
      set(val) {
        this.name = val
        if (this.autoChangeCode && this.isMounted) this.system_name = toUpperCaseWithUnderscores(val)
      },
    },
    system_nameCalc: {
      get() {
        return this.system_name || ''
      },
      set(val) {
        this.system_name = val
        this.autoChangeCode = false
      },
    },
  },
  watch: {
    metadata(newData) {
      this.parseJson(newData)
    },
    source_type(newType) {
      if (newType === 'Salesforce') {
        this.customFields.object_api_name = 'Knowledge__kav'
        this.customFields.output_config = '["{Summary}"]'
      } else {
        delete this.customFields.object_api_name
        delete this.customFields.output_config
      }
    },
    // When provider data loads asynchronously (TanStack Query), apply provider config
    providerItems(items) {
      if (this.providerSystemName && items?.length && !this.source_type) {
        const provider = items.find((p) => p.system_name === this.providerSystemName)
        if (provider) {
          this.source_type = provider.type
          this.applyProviderConnectionParams(provider)
        }
      }
    },
    supportSemanticSearch(newValue) {
      if (newValue) {
        this.$refs.semantic_search_supportedRef?.resetValidation()
        this.$refs.support_keyword_searchRef?.resetValidation()
      }
    },
    supportKeywordSearch(newValue) {
      if (newValue) {
        this.$refs.support_keyword_searchRef?.resetValidation()
        this.$refs.semantic_search_supportedRef?.resetValidation()
      }
    },
  },
  mounted() {
    this.isMounted = true

    // Clear knowledge store to prevent stale data (e.g. uploaded_files) from
    // a previously viewed knowledge source leaking into the new creation form.
    if (!this.copy) {
      this.tempEntity = null
      this.collectionDetailStore.setEntity(null)
    }

    // Set provider_system_name from providerSystemName prop if provided
    if (this.providerSystemName) {
      this.provider_system_name = this.providerSystemName
      const provider = this.providerItems?.find((p) => p.system_name === this.providerSystemName)
      if (provider) {
        this.source_type = provider.type // Set source_type to match provider's type
        // Apply provider connection params
        this.applyProviderConnectionParams(provider)
      }
    }

    if (this.copy) {
      this.customFields = reactive(cloneDeep(this.currentRaw))
      this.name = this.customFields?.name + '_COPY'
      this.description = this.customFields?.description + '_COPY'
      this.system_name = this.customFields?.system_name + '_COPY'
      this.source_type = this.customFields?.source_type
      this.show_in_qa = this.customFields?.show_in_qa
      this.category = this.customFields?.category
      this.type = this.customFields?.type
      this.chunkSize = this.customFields?.chunk_size ?? ''
      this.chunkOverlap = this.customFields?.chunk_overlap ?? ''
      this.ai_model = this.customFields?.ai_model
      this.provider_system_name = this.customFields?.provider_system_name || ''
      delete this.customFields.id
      delete this.customFields.created
      delete this.customFields.last_synced
    } else {
      this.ai_model = this.defaultModel
    }
  },
  methods: {
    onProviderChange(providerSystemName) {
      if (!providerSystemName) {
        // Clear provider-related data when provider is deselected
        this.source_type = ''
        return
      }

      const provider = this.providerItems?.find((p) => p.system_name === providerSystemName)
      if (provider) {
        this.source_type = provider.type // Set source_type to match provider's type
        this.applyProviderConnectionParams(provider)
      }
    },
    applyProviderConnectionParams(provider) {
      // DO NOT copy endpoint or credentials to source - these are security-critical fields
      // that must only come from provider configuration on the backend.
      // The backend will automatically merge provider config (including endpoint and credentials)
      // when processing the knowledge source.

      // Apply ONLY non-security connection_config parameters to source fields
      // (e.g., service-specific URLs like search_api_url, pdf_api_url, base_slug)
      if (provider.connection_config) {
        const securityFields = new Set([
          'endpoint',
          'client_id',
          'client_secret',
          'tenant',
          'thumbprint',
          'private_key',
          'username',
          'password',
          'token',
          'security_token',
          'api_token',
          'api_key',
        ])

        Object.entries(provider.connection_config).forEach(([key, value]) => {
          // Only copy non-security fields
          if (!securityFields.has(key)) {
            this.source = { ...this.source, [key]: value }
          }
        })
      }

      // Note: secrets_encrypted and endpoint are handled on backend side only
    },
    next(step) {
      if (!this.validateFields()) return
      this.stepper = step
    },
    indexingRules() {
      return () => {
        return this.supportSemanticSearch || this.supportKeywordSearch || 'At least one indexing option must be enabled'
      }
    },
    async createNew(sync) {
      if (!this.validateFields()) return

      this.loadingCreate = true

      const {
        metadata,
        name,
        source,
        show_in_qa,
        category,
        type,
        system_name,
        description,
        ai_model,
        chunkingStrategy,
        chunkSize,
        chunkOverlap,
        chunkTransformationEnabled,
        chunkTransformationPromptTemplate,
        chunkTransformationMethod,
        chunkUsageMethod,
        supportSemanticSearch,
        supportKeywordSearch,
        provider_system_name,
      } = this

      // Transform Documentation source fields
      const transformedSource = this.transformSourceFields(source)

      // Merge temp-uploaded files (file_id refs) from store into source payload
      const tempUploadedFiles = this.collectionDetailStore.entity?.source?.uploaded_files || []
      if (tempUploadedFiles.length) {
        transformedSource.uploaded_files = [
          ...(transformedSource.uploaded_files || []),
          ...tempUploadedFiles,
        ]
      }

      const merged_metadata = {
        ...JSON.parse(metadata ?? {}),
        ...this.customFields,
        name,
        source: transformedSource,
        show_in_qa: String(show_in_qa),
        category,
        type,
        system_name,
        description,
        ai_model,
        provider_system_name: provider_system_name || undefined, // Link to provider by system_name
        chunking: {
          strategy: chunkingStrategy,
          chunk_size: parseInt(chunkSize),
          chunk_overlap: parseInt(chunkOverlap),
          transformation_enabled: chunkTransformationEnabled,
          transformation_prompt_template: chunkTransformationPromptTemplate,
          transformation_method: chunkTransformationMethod,
          chunk_usage_method: chunkUsageMethod,
        },
        indexing: {
          semantic_search_supported: supportSemanticSearch,
          fulltext_search_supported: supportKeywordSearch,
        },
      }
      const { id: inserted_id } = await this.createCollection(merged_metadata)

      notify.success('Knowledge source has been created.')

      if (sync) {
        await this.createOneTimeJob()

        notify.success('Sync job has been created.')
      }

      // Create scheduled job if enabled
      const job = await this.createJob(inserted_id)

      // Set the knowledge state with the created item data including job_id
      // This ensures the detail page has the correct data on navigation
      const knowledgeData = {
        ...merged_metadata,
        id: inserted_id,
        job_id: job?.job_id || null,
      }
      this.tempEntity = knowledgeData

      // Navigate to the detail page
      const targetPath = `/knowledge-sources/${inserted_id}`
      this.$router.push(targetPath)

      // Call cancelCreate after navigation initiated
      this.$nextTick(() => {
        this.resetState()
        this.$emit('cancel', false)
      })
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    async createJob(inserted_id) {
      if (this.scheduleEnabled) {
        const hour = this.form.time.value
        let cron
        if (this.form.interval === 'custom') {
          // Parse custom cron string: minute hour day month day_of_week
          const parts = this.form.customCron.trim().split(/\s+/)
          cron = {
            minute: parts[0] || '*',
            hour: parts[1] || '*',
            day: parts[2] || '*',
            month: parts[3] || '*',
            day_of_week: parts[4] || '*',
          }
        } else if (this.form.interval === 'every_5_minutes') {
          cron = { minute: '*/5', hour: '*', day_of_month: '*' }
        } else if (this.form.interval === 'hourly') {
          cron = { minute: '0', hour: '*', day_of_month: '*' }
        } else if (this.form.interval === 'daily') {
          cron = { minute: '0', hour, day_of_month: '*' }
        } else {
          // weekly
          cron = { minute: '0', hour, day_of_month: '*', day_of_week: this.form.day }
        }

        const schedulerEndpoint = this.appStore.config?.scheduler?.endpoint
        const schedulerService = this.appStore.config?.scheduler?.service
        const schedulerCredentials = this.appStore.config?.scheduler?.credentials
        const jobResponse = await fetchData({
          endpoint: schedulerEndpoint,
          service: `${schedulerService}/create-job`,
          method: 'POST',
          body: JSON.stringify({
            name: this.form.name,
            job_type: 'recurring',
            cron,
            notification_email: this.form.error_email,
            interval: this.form.interval,
            run_configuration: {
              type: 'sync_collection',
              params: {
                system_name: this.system_name,
              },
            },
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          }),
          credentials: schedulerCredentials,
          headers: { 'Content-Type': 'application/json' },
        })
        const job = await jobResponse.json()
        await this.updateCollection({ id: inserted_id, data: { job_id: job.job_id } })
        return job
      }
      return null
    },
    async createOneTimeJob() {
      let jobData = {
        name: `Sync ${this.name}`,
        job_type: 'one_time_immediate',
        notification_email: '',
        run_configuration: {
          type: 'sync_collection',
          params: {
            system_name: this.system_name,
          },
        },
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }

      const endpoint = this.appStore.config?.scheduler?.endpoint
      const service = this.appStore.config?.scheduler?.service
      const credentials = this.appStore.config?.scheduler?.credentials
      const response = await fetchData({
        endpoint,
        service: `${service}/create-job`,
        method: 'POST',
        body: JSON.stringify(jobData),
        credentials,
        headers: { 'Content-Type': 'application/json' },
      })
      const job = await response.json()
      notify.success('Sync job has been created.')
      return job
    },
    transformSourceFields(source) {
      // Transform Documentation source fields from comma-separated strings to arrays
      if (source?.source_type === 'Documentation') {
        const transformed = { ...source }

        // Convert languages from string to array
        if (transformed.languages && typeof transformed.languages === 'string') {
          transformed.languages = transformed.languages
            .split(',')
            .map((lang) => lang.trim())
            .filter((lang) => lang.length > 0)
        }

        // Convert sections from string to array
        if (transformed.sections && typeof transformed.sections === 'string') {
          transformed.sections = transformed.sections
            .split(',')
            .map((section) => section.trim())
            .filter((section) => section.length > 0)
        }

        // Convert max_depth to integer if provided
        if (transformed.max_depth) {
          transformed.max_depth = parseInt(transformed.max_depth) || 5
        }

        return transformed
      }

      return source
    },
    parseJson(str) {
      try {
        JSON.parse(str)
      } catch {
        this.jsonError = true
        return false
      }
      this.jsonError = false
      return true
    },
    onDialogHide() {
      this.resetState()
      this.$emit('cancel')
    },
    async cancelCreate() {
      this.$emit('cancel', false)
      this.resetState()
    },
    resetState() {
      this.errors = {}
      this.jsonError = false
      this.loadingCreate = false

      this.name = ''
      this.title = ''
      this.type = ''
      this.category = ''
      this.show_in_qa = false
      this.source_type = ''
      this.source = {}
      this.provider_system_name = ''
      this.metadata = '{}'
      this.stepper = 0

      this.tempEntity = null
      this.collectionDetailStore.setEntity(null)

      this.customFields = {}

      this.requiredFields.forEach((field) => {
        this.$refs[`${field}Ref`]?.resetValidation()
      })
    },
  },
})
</script>
