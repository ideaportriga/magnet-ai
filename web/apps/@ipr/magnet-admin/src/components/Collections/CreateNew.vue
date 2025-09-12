<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")')
  q-card.card-style.q-px-md(style='min-width: 800px')
    q-card-section.card-section-style.q-mb-md
      .row
        .col
          .km-heading-7 New Knowledge Source
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      .row.items-center.justify-center
        km-stepper.full-width(
          :steps='[ { step: 0, description: "Basic configuration", icon: "pen" }, { step: 1, description: "Chunking settings", icon: "circle" }, { step: 2, description: "Indexing settings", icon: "circle" }, { step: 3, description: "Schedule", icon: "schedule" }, ]',
          :stepper='stepper'
        )
      .column.full-width(v-if='stepper === 0')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
        .full-width.q-mb-md
          km-input(v-model='nameCalc', ref='nameRef', :rules='config.name.rules')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 System name
        .full-width.q-mb-md
          km-input(v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Source type
        .full-width.q-mb-md
          km-select(:options='config.source_type.options', v-model='source_type', ref='source_typeRef', :rules='config.source_type.rules')
        template(v-for='item in config.source_type?.children[source_type]')
          .col
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ item.label }}
            .q-mb-md
              component(:is='item.component', v-model='source[item.field]')
      .column.full-width(v-if='stepper === 1')
        .col.q-pt-8.q-mt-sm
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Chunking strategy
          km-select(
            v-model='chunkingStrategy',
            ref='chunking_strategyRef',
            placeholder='Chunking strategy',
            :options='config.chunking_strategy.options',
            :rules='config.chunking_strategy.rules',
            emit-value,
            map-options,
            option-value='value',
            option-label='label'
          )
          .km-description.text-secondary-text.q-mt-xs.q-ml-sm Chunking strategy defines how documents are divided into smaller chunks for better search results.
        .row.q-gap-16(v-if='chunkingStrategy === "recursive_character_text_splitting"')
          .col.q-pt-8.q-mt-sm
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 Chunk size
            km-input(type='number', v-model='chunkSize', ref='maxChunkRef')
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm Defines the maximum number of characters in each chunk when splitting.
          .col.q-pt-8.q-mt-sm
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 Chunk overlap
            km-input(type='number', v-model='chunkOverlap', ref='maxChunkRef')
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm Defines the overlap (in characters) between chunks when splitting.
        .col.q-pt-8.q-mt-md.q-pl-8
          .row.items-baseline
            .col-auto.q-mr-sm
              .km-field.text-secondary-text.absolute.q-ml-40 Enable chunk LLM transformation
              q-toggle(v-model='chunkTransformationEnabled', dense)
        .column.q-gap-16.q-pt-2.q-mt-sm(v-if='chunkTransformationEnabled')
          .col(v-if='chunkTransformationEnabled')
            km-select(
              v-model='chunkTransformationPromptTemplate',
              placeholder='Select a prompt template',
              :options='chunkTransformationPromptTemplateOptions',
              hasDropdownSearch,
              emit-value,
              map-options,
              option-value='system_name'
            )
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm Transforms document chunks before embedding to improve search quality. Note that this transformation can greatly increase latency and cost.
          .col
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 How to apply transformation
            km-select(
              v-model='chunkTransformationMethod',
              :options='config.chunk_transformation_method.options',
              placeholder='Select how to apply transformation',
              emit-value,
              map-options,
              option-value='value',
              option-label='label',
              :disabled='isDisable'
            )
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm Defines how transformation is applied to the chunk. For example, you can prepend/append generated text to the chunk, or replace chunk content entirely.
          .col
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 How to use chunks
            km-select(
              v-model='chunkUsageMethod',
              :options='config.chunk_usage_method.options',
              placeholder='Select how to use chunks',
              emit-value,
              map-options,
              option-value='value',
              option-label='label',
              :disabled='isDisable'
            )
            .km-description.text-secondary-text.q-mt-xs.q-ml-sm Defines which chunk is used for indexing and which for retrieval.
      .column.full-width(v-if='stepper === 2')
        .km-description.q-mt-sm.q-pl-8 Enabling both semantic search and full-text search activates hybrid search, which combines the benefits of both approaches, but will increase latency and cost of the search and the source sync.
        .col.q-pt-8.q-mt-md.q-pl-8
          .row.items-baseline
            .col-auto.q-mr-sm
              .km-field.text-secondary-text.absolute.q-ml-40 Support semantic search
              km-toggle(v-model='supportSemanticSearch', ref='semantic_search_supportedRef', :rules='[indexingRules()]', dense)
        .km-description.text-secondary-text.q-mt-xs.q-ml-sm Create vector embeddings to support semantic search, which allows you to search for documents based on their meaning rather than just exact matches.
        .col.q-pt-8.q-mt-sm(v-if='supportSemanticSearch')
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Embedding Model
          km-select(
            height='auto',
            minHeight='36px',
            placeholder='Embedding Model',
            v-model='ai_model',
            :options='modelOptions',
            optionLabel='display_name',
            emit-value,
            mapOptions,
            optionValue='system_name'
          )
        .col.q-pt-8.q-mt-md.q-pl-8
          .row.items-baseline
            .col-auto.q-mr-sm
              .km-field.text-secondary-text.absolute.q-ml-40 Support full-text search
              km-toggle(v-model='supportFullTextSearch', ref='support_full_text_searchRef', :rules='[indexingRules()]', dense)
        .km-description.text-secondary-text.q-mt-xs.q-ml-sm Toggling this option enables full-text search, which can be beneficial for some use cases. Note that full-text search capabilities depend on the underlying database configuration and may vary across different environments.
      .column.full-width(v-if='stepper === 3')
        .km-button-xs-text.text-secondary-text Schedule sync
          q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='scheduleEnabled', ref='scheduleEnabledRef')
          .km-description.text-secondary-text Automatically sync knowledge source
          template(v-if='scheduleEnabled')
            .q-px-md.q-mt-md
              .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md Job interval
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
                  .km-field.text-secondary-text Every
                  km-select(v-model='form.day', :options='days')
                .row.items-center.q-gap-8
                  .km-field.text-secondary-text at
                  km-select(v-model='form.time', :options='times')
              .row.q-mt-md.items-center
                km-checkbox(size='40px', v-model='form.enabled')
                .km-field Send error notifications
              .km-tiny.text-secondary-text Email admin in case of syncing errors. Applies only for scheduled sync.
              template(v-if='form.enabled')
                .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md Error notification email
                .full-width
                  km-input(height='30px', v-model='form.error_email', ref='errorEmailRef')

      .row.q-mt-lg
        .col-auto
          km-btn(flat, label='Cancel', color='primary', @click='cancelCreate')
        .col
        .col-auto
          .row.q-gap-16.no-wrap.items-center.q-py-4
            template(v-if='stepper === 0')
              km-btn(label='Next', @click='next(1)')
            template(v-else-if='stepper === 1')
              km-btn(flat, label='Back', @click='stepper = 0')
              km-btn(label='Next', @click='next(2)')
            template(v-else-if='stepper === 2')
              km-btn(flat, label='Back', @click='stepper = 1')
              km-btn(label='Next', @click='next(3)')
            template(v-else-if='stepper === 3')
              km-btn(flat, label='Back', @click='stepper = 2', :disable='loadingCreate')
              km-btn(label='Save', @click='createNew(false)', :disable='loadingCreate')
              km-btn(label='Save & Sync', @click='createNew(true)', :disable='loadingCreate')
    q-inner-loading(:showing='loadingCreate', color='primary', size='50px')
</template>
<script>
import { defineComponent, ref, reactive } from 'vue'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@shared/utils/validationRules'
import { useChroma } from '@shared'
import { toUpperCaseWithUnderscores } from '@shared'

export default defineComponent({
  props: {
    showNewDialog: Boolean,
    copy: Boolean,
  },
  emits: ['cancel'],
  setup() {
    const { requiredFields, config, ...useCollection } = useChroma('collections')
    const { items: promptTemplateItems } = useChroma('promptTemplates')
    const intervals = [
      { label: 'Hourly', value: 'hourly' },
      { label: 'Daily', value: 'daily' },
      { label: 'Weekly', value: 'weekly' },
    ]
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    const times = Array.from({ length: 24 }, (_, i) => ({ label: `${i.toString().padStart(2, '0')}:00`, value: i.toString().padStart(2, '0') }))
    return {
      customFields: ref({}),
      metadata: ref('{}'),
      show_in_qa: ref(false),
      category: ref(''),
      type: ref(''),
      name: ref(''),
      system_name: ref(''),
      description: ref(''),
      source: ref({}),

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

      loadingCreate: ref(false),
      jsonError: ref(false),
      required,
      minLength,
      // required_fields: ['name', 'title', 'source_type' ,'category','type'],
      requiredFields,
      config,
      useCollection,
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
      }),
      promptTemplateItems,
      // New reactive property for sync confirmation display
    }
  },
  computed: {
    source_type: {
      get() {
        return this.source?.source_type || ''
      },
      set(val) {
        this.source = { ...this.source, source_type: val }
      },
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
    modelOptions() {
      return (this.$store.getters['chroma/model'].items || []).filter((el) => el.type === 'embeddings')
    },
    currentRaw() {
      return this.$store.getters.knowledge
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
    supportSemanticSearch(newValue) {
      if (newValue) {
        this.$refs.semantic_search_supportedRef?.resetValidation()
        this.$refs.support_full_text_searchRef?.resetValidation()
      }
    },
    supportFullTextSearch(newValue) {
      if (newValue) {
        this.$refs.support_full_text_searchRef?.resetValidation()
        this.$refs.semantic_search_supportedRef?.resetValidation()
      }
    },
  },
  mounted() {
    this.isMounted = true
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
      delete this.customFields.id
      delete this.customFields.created
      delete this.customFields.last_synced
    } else {
      this.ai_model = this.defaultModel
    }
  },
  methods: {
    next(step) {
      if (!this.validateFields()) return
      this.stepper = step
    },
    indexingRules() {
      return () => {
        return this.supportSemanticSearch || this.supportFullTextSearch || 'At least one indexing option must be enabled'
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
        supportFullTextSearch,
      } = this

      const merged_metadata = {
        ...JSON.parse(metadata ?? {}),
        ...this.customFields,
        name,
        source,
        show_in_qa: String(show_in_qa),
        category,
        type,
        system_name,
        description,
        ai_model,
        chunking: {
          strategy: chunkingStrategy,
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap,
          transformation_enabled: chunkTransformationEnabled,
          transformation_prompt_template: chunkTransformationPromptTemplate,
          transformation_method: chunkTransformationMethod,
          chunk_usage_method: chunkUsageMethod,
        },
        indexing: {
          semantic_search_supported: supportSemanticSearch,
          fulltext_search_supported: supportFullTextSearch,
        },
      }
      const { id:inserted_id } = await this.useCollection.create(JSON.stringify(merged_metadata))

      this.$q.notify({
        position: 'top',
        message: 'Knowledge source has been created.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })

      if (sync) {
        await this.createOneTimeJob()

        this.$q.notify({
          position: 'top',
          message: 'Sync job has been created.',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      }

      await this.createJob(inserted_id)

      // Navigate first, then clean up
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
        const cron =
          this.form.interval === 'hourly'
            ? { minute: '0', hour: '*', day_of_month: '*' }
            : this.form.interval === 'daily'
              ? { minute: '0', hour, day_of_month: '*' }
              : { minute: '0', hour, day_of_month: '*', day_of_week: this.form.day }

        const job = await this.$store.dispatch('createAndRunJobScheduler', {
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
          // get user timezone for apscheduler
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        })
        await this.useCollection.update({ id: inserted_id, data: { job_id: job.job_id } })
        await this.$store.commit('updateKnowledge', { job_id: job.job_id })
      }
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

      const job = await this.$store.dispatch('createAndRunJobScheduler', jobData)
      this.$q.notify({
        position: 'top',
        message: 'Sync job has been created.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      return job
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
      this.metadata = '{}'

      this.customFields = {}

      this.requiredFields.forEach((field) => {
        this.$refs[`${field}Ref`]?.resetValidation()
      })
    },
  },
})
</script>
