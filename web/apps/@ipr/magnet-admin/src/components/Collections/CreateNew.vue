<template lang="pug">
q-dialog(:model-value='showNewDialog', @hide='onDialogHide')
  q-card.card-style.q-px-md(style='min-width: 800px')
    q-card-section.card-section-style.q-mb-md
      .row
        .col
          .km-heading-7 {{ m.dialog_newKnowledgeSource() }}
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      .row.items-center.justify-center
        km-stepper.full-width(
          :steps='[ { step: 0, description: m.collections_basicConfiguration(), icon: "pen" }, { step: 1, description: m.collections_chunkingSettings(), icon: "circle" }, { step: 2, description: m.collections_indexingSettings(), icon: "circle" }, { step: 3, description: m.collections_schedule(), icon: "schedule" }, ]',
          :stepper='stepper'
        )
      .column.full-width(v-if='stepper === 0')
        //- .km-field.text-secondary-text.q-pb-xs.q-pl-8 Knowledge Source Provider (Optional)
        //- .full-width.q-mb-md
        //-   km-select(
        //-     v-model='provider_system_name',
        //-     :options='providerOptions',
        //-     placeholder='Select provider (optional)',
        //-     clearable,
        //-     emit-value,
        //-     map-options,
        //-     option-value='system_name',
        //-     option-label='name',
        //-     @update:model-value='onProviderChange',
        //-     :disable='!!providerSystemName'
        //-   )
        //-   .km-description.text-secondary-text.q-mt-xs.q-ml-sm(v-if='providerSystemName') Provider is pre-selected and cannot be changed when creating under a specific provider
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_name() }}
        .full-width.q-mb-md
          km-input(data-test='name-input', v-model='nameCalc', ref='nameRef', :rules='config.name.rules')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_systemName() }}
        .full-width.q-mb-md
          km-input(data-test='system-name-input', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
        //- .km-field.text-secondary-text.q-pb-xs.q-pl-8 Source type
        //- .full-width.q-mb-md
        //-   km-select(:options='dynamicSourceTypeOptions', v-model='source_type', ref='source_typeRef', :rules='config.source_type.rules', :disable='!!selectedProvider')
        //-   .km-description.text-secondary-text.q-mt-xs.q-ml-sm(v-if='selectedProvider') Source type is automatically set based on the selected provider
        template(v-for='item in dynamicSourceTypeChildren[source_type]')
          .col
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ item.label }}
            .q-mb-md
              component(:is='item.component', v-model='source[item.field]', ref='sourceComponents')
      .column.full-width(v-if='stepper === 1')
        .col.q-pt-8.q-mt-sm
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.collections_chunkingStrategy() }}
          km-select(
            v-model='chunkingStrategy',
            ref='chunking_strategyRef',
            :placeholder='m.collections_chunkingStrategy()',
            :options='config.chunking_strategy.options',
            :rules='config.chunking_strategy.rules',
            emit-value,
            map-options,
            option-value='value',
            option-label='label'
          )
          .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_chunkingStrategyHint() }}
        .row.q-gap-16(v-if='chunkingStrategy === "recursive_character_text_splitting"')
          .col.q-pt-8.q-mt-sm
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.collections_chunkSize() }}
            km-input(type='number', v-model='chunkSize', ref='maxChunkRef')
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_chunkSizeHint() }}
          .col.q-pt-8.q-mt-sm
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.collections_chunkOverlap() }}
            km-input(type='number', v-model='chunkOverlap', ref='maxChunkRef')
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_chunkOverlapHint() }}
        .col.q-pt-8.q-mt-md.q-pl-8
          .row.items-baseline
            .col-auto.q-mr-sm
              .km-field.text-secondary-text.absolute.q-ml-40 {{ m.collections_enableChunkLlmTransformation() }}
              q-toggle(v-model='chunkTransformationEnabled', dense)
        .column.q-gap-16.q-pt-2.q-mt-sm(v-if='chunkTransformationEnabled')
          .col(v-if='chunkTransformationEnabled')
            km-select(
              v-model='chunkTransformationPromptTemplate',
              :placeholder='m.collections_selectPromptTemplate()',
              :options='chunkTransformationPromptTemplateOptions',
              hasDropdownSearch,
              emit-value,
              map-options,
              option-value='system_name'
            )
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_chunkTransformationPromptHint() }}
          .col
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.collections_howToApplyTransformation() }}
            km-select(
              v-model='chunkTransformationMethod',
              :options='config.chunk_transformation_method.options',
              :placeholder='m.collections_selectHowToApplyTransformation()',
              emit-value,
              map-options,
              option-value='value',
              option-label='label',
              :disabled='isDisable'
            )
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_howToApplyTransformationHint() }}
          .col
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.collections_howToUseChunks() }}
            km-select(
              v-model='chunkUsageMethod',
              :options='config.chunk_usage_method.options',
              :placeholder='m.collections_selectHowToUseChunks()',
              emit-value,
              map-options,
              option-value='value',
              option-label='label',
              :disabled='isDisable'
            )
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_howToUseChunksHint() }}
      .column.full-width(v-if='stepper === 2')
        .km-description.q-mt-sm.q-pl-8 {{ m.collections_hybridSearchHint() }}
        .col.q-pt-8.q-mt-md.q-pl-8
          .row.items-baseline
            .col-auto.q-mr-sm
              .km-field.text-secondary-text.absolute.q-ml-40 {{ m.collections_supportSemanticSearch() }}
              km-toggle(v-model='supportSemanticSearch', ref='semantic_search_supportedRef', :rules='[indexingRules()]', dense, :disable='true')
        .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_semanticSearchHint() }}
        .col.q-pt-8.q-mt-sm(v-if='supportSemanticSearch')
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.collections_embeddingModel() }}
          km-select(
            height='auto',
            minHeight='36px',
            :placeholder='m.collections_embeddingModel()',
            v-model='ai_model',
            :options='modelOptions',
            optionLabel='display_name',
            emit-value,
            mapOptions,
            optionValue='system_name'
          )
            template(#option='{ itemProps, opt, selected, toggleOption }')
              q-item.ba-border(v-bind='itemProps', dense, @click='toggleOption(opt)')
                q-item-section
                  q-item-label.km-label {{ opt.display_name }}
                  .row.q-mt-xs(v-if='opt.provider_system_name')
                    q-chip(color='primary-light', text-color='primary', size='sm', dense) {{ opt.provider_system_name }}
        .col.q-pt-8.q-mt-md.q-pl-8
          .row.items-baseline
            .col-auto.q-mr-sm
              .km-field.text-secondary-text.absolute.q-ml-40 {{ m.collections_supportKeywordSearch() }}
              km-toggle(v-model='supportKeywordSearch', ref='support_keyword_searchRef', :rules='[indexingRules()]', dense)
        .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.collections_keywordSearchHint() }}
      .column.full-width(v-if='stepper === 3')
        .km-button-xs-text.text-secondary-text {{ m.collections_scheduleSync() }}
          q-toggle(height='30px', v-model='scheduleEnabled', ref='scheduleEnabledRef')
          .km-description.text-secondary-text {{ m.collections_automaticallySyncKnowledgeSource() }}
          template(v-if='scheduleEnabled')
            .q-px-md.q-mt-md
              .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md {{ m.collections_jobInterval() }}
              .full-width
                q-btn-toggle(
                  v-model='form.interval',
                  toggle-color='primary-light',
                  :options='intervals',
                  dense,
                  text-color='text-weak',
                  toggle-text-color='primary'
                )
              .row.q-mt-md.items-center.q-gap-8.q-pl-8(v-if='form.interval === "daily" || form.interval === "weekly"')
                .row.items-center.q-gap-8(v-if='form.interval === "weekly"')
                  .km-field.text-secondary-text {{ m.collections_every() }}
                  km-select(v-model='form.day', :options='days')
                .row.items-center.q-gap-8
                  .km-field.text-secondary-text {{ m.collections_at() }}
                  km-select(v-model='form.time', :options='times')
              //- Custom cron input
              .q-mt-md.q-pl-8(v-if='form.interval === "custom"')
                .km-field.text-secondary-text.q-pb-xs {{ m.collections_cronExpression() }}
                km-input(height='30px', v-model='form.customCron', :placeholder='m.common_cronExpression()')
                .km-tiny.text-secondary-text.q-mt-xs {{ m.collections_cronFormatHint() }}
              .row.q-mt-md.items-center
                km-checkbox(size='40px', v-model='form.enabled')
                .km-field {{ m.collections_sendErrorNotifications() }}
              .km-tiny.text-secondary-text {{ m.collections_errorNotificationHint() }}
              template(v-if='form.enabled')
                .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md {{ m.collections_errorNotificationEmail() }}
                .full-width
                  km-input(height='30px', v-model='form.error_email', ref='errorEmailRef')

      .row.q-mt-lg
        .col-auto
          km-btn(data-test='cancel-btn', flat, :label='m.common_cancel()', color='primary', @click='cancelCreate')
        .col
        .col-auto
          .row.q-gap-16.no-wrap.items-center.q-py-4
            template(v-if='stepper === 0')
              km-btn(data-test='next-btn', :label='m.common_next()', @click='next(1)')
            template(v-else-if='stepper === 1')
              km-btn(data-test='back-btn', flat, :label='m.common_back()', @click='stepper = 0')
              km-btn(data-test='next-btn', :label='m.common_next()', @click='next(2)')
            template(v-else-if='stepper === 2')
              km-btn(data-test='back-btn', flat, :label='m.common_back()', @click='stepper = 1')
              km-btn(data-test='next-btn', :label='m.common_next()', @click='next(3)')
            template(v-else-if='stepper === 3')
              km-btn(data-test='back-btn', flat, :label='m.common_back()', @click='stepper = 2', :disable='loadingCreate')
              km-btn(data-test='save-btn', :label='m.common_save()', @click='createNew(false)', :disable='loadingCreate')
              km-btn(data-test='save-and-sync-btn', :label='m.common_saveAndSync()', @click='createNew(true)', :disable='loadingCreate')
    q-inner-loading(:showing='loadingCreate', color='primary', size='50px')
</template>
<script>
import { defineComponent, ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@/utils/validationRules'
import { toUpperCaseWithUnderscores, fetchData } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
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
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
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
