<template lang="pug">
.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(style='max-width: 500px; min-width: 500px !important')
  .column.full-height
    .col-auto.km-heading-7.q-mb-xs
      .row
        .col Preview
        .col-auto
          km-btn(flat, simple, label='Evaluate', iconSize='16px', icon='fas fa-clipboard-check', @click='showNewDialog = true')
    q-separator.q-mb-md
    .col-auto
      .km-heading-5.text-text-grey Input

      km-input(
        data-test='preview-input',
        ref='input',
        rows='10',
        placeholder='Type your text here',
        :model-value='testText',
        @input='testText = $event',
        @keydown.enter='submit',
        border-radius='8px',
        height='36px',
        type='textarea'
      )
      .km-field.text-secondary-text Plain text or JSON

      .q-mt-md
        q-file(outlined, clearable, label='File upload', v-model='files', multiple, accept='.pdf', @update:model-value='handleFilesUpload', :loading="fileUploadInProgress")
          template(v-slot:append)
            q-icon(name='attach_file')

      .row.justify-end
        .col-auto.q-my-md
          q-btn.border-radius-6.q-mb-4(
            data-test='preview-btn',
            color='primary',
            :disable='!testText?.length',
            @click='submit',
            unelevated,
            padding='6px 7px',
            style='maxheight: 28px'
          )
            template(v-slot:default)
              q-icon(name='fas fa-paper-plane', size='16px')
      .col-auto
        q-separator
        //- OUTPUT
        .row.q-py-8.items-center
          .col
            .km-heading-5.text-text-grey Output
          .col.row.justify-center
            km-btn.width-100(
              v-if='detailedResponse',
              color='primary',
              iconColor='primary',
              labelClass='km-title',
              label='View costs & latency',
              @click='showDetails = true',
              flat,
              iconSize='16px',
              hoverBg='primary-bg'
            )
          .col-auto
            q-toggle(v-model='markdown', label='Markdown', color='primary')
    q-scroll-area.full-height.col
      template(v-if='loading')
        .row.justify-center
          q-spinner-dots(size='62px', color='primary')
      template(v-else-if='text !== undefined')
        .row.no-wrap.q-pt-18
          .col-auto
            q-avatar(text-color='white', size='36px')
              km-icon(:name='"magnet"', width='20', height='22')
          .col.border-radius-12.q-pb-md
            .q-py-6.q-px-12
              km-markdown(v-if='markdown', :source='text') 
              pre(v-if='!markdown') {{ text }}

    .col-auto
      .row.items-center
        .col-auto
          km-btn(flat, simple, label='Clear preview', iconSize='16px', icon='fas fa-eraser', @click='clearText')
        q-space
        .col-auto
          km-btn(icon='fas fa-copy', iconSize='16px', size='sm', flat, @click='copy', label='Copy', tooltip='Copy')

  evaluation-jobs-create-new(
    :showNewDialog='showNewDialog',
    @create='createEvaluation',
    @cancel='showNewDialog = false',
    v-if='showNewDialog',
    :system_name='promptSystemName',
    type='prompt_template'
  )
  //- TODO: Add a new component for this (same as in Configuration/Drawer.vue)
  km-popup-confirm(
    :visible='showEvaluationCreateDialog',
    confirmButtonLabel='View Evaluation',
    notificationIcon='far fa-circle-check',
    cancelButtonLabel='Cancel',
    @cancel='showEvaluationCreateDialog = false',
    @confirm='navigateToEval()'
  )
    .row.item-center.justify-center.km-heading-7 Evaluation has started!
    .row.text-center.justify-center It may take some time for the Evaluation to finish.
    .row.text-center.justify-center You’ll be able to view run results on the Evaluation screen.
  km-popup-confirm(
    :visible='showDetails',
    title='Costs & Latency',
    confirmButtonLabel='OK',
    cancelButtonLabel='Cancel',
    @cancel='showDetails = false',
    @confirm='showDetails = false'
  )
    prompts-cost-popup(:record='detailedResponse')
</template>
<script>
import { defineComponent, ref } from 'vue'
import { copyToClipboard } from 'quasar'
import { useStore } from 'vuex'
import { fetchData } from '@shared'

export default defineComponent({
  props: ['open'],
  emits: ['update:open'],
  setup() {
    const store = useStore()

    return {
      store,
      detailedResponse: ref(undefined),
      showDetails: ref(false),
      testText: ref(''),
      text: ref(undefined),
      loading: ref(false),
      showNewDialog: ref(false),
      showEvaluationCreateDialog: ref(false),
      markdown: ref(false),
      evaluationIds: ref(''),
      evaluationResults: ref({}),
      files: ref([]),
      fileUploadInProgress: ref(false),
    }
  },
  computed: {
    selectedRow() {
      return this.$store.getters.promptTemplate
    },
    selectedRowDetails() {
      return { name: this.$store.getters.promptTemplate?.name, ...this.$store.getters.promptTemplateVariant }
    },
    promptSystemName() {
      return this.selectedRow?.system_name
    },
    promptTemplateTestSetItem() {
      return this.$store.getters.promptTemplateTestSetItem
    },
  },
  watch: {
    promptTemplateTestSetItem: {
      deep: true,
      handler(next, prev) {
        if (prev?.user_input !== next?.user_input) {
          this.testText = next?.user_input || ''
        }
      },
    },
    selectedRow: {
      deep: true,
      handler(next, prev) {
        if (prev?.id !== next?.id) {
          this.text = undefined
          this.testText = ''
        }
      },
    },
  },
  methods: {
    navigateToEval() {
      const query = {
        job_id: this.evaluationResults?.job_id,
      }
      const path = '/evaluation-jobs'
      this.$router.push({ path, query })
    },
    createEvaluation(obj) {
      this.evaluationResults = obj
      this.showNewDialog = false
      if (this.evaluationResults) this.showEvaluationCreateDialog = true
    },
    copy() {
      copyToClipboard(this.text || '')
      this.$q.notify({
        position: 'top',
        message: 'Output has been copied to clipboard',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    clearText() {
      this.text = undefined
    },

    async submit(event) {
      if (event.shiftKey) return
      event.preventDefault()
      this.text = undefined
      this.loading = true

      this.detailedResponse =
        (await this.$store.dispatch('enhanceTextDetails', {
          name: this.selectedRowDetails?.name,
          text: this?.testText || '',
          prompt: this.selectedRowDetails?.text || '',
          temperature: this.selectedRowDetails?.temperature,
          model: this.selectedRowDetails?.model,
          topP: this.selectedRowDetails?.topP,
          maxTokens: parseInt(this.selectedRowDetails?.maxTokens),
          response_format: this.selectedRowDetails?.response_format,
          system_name_for_model: this.selectedRowDetails?.system_name_for_model,
          system_name_for_prompt_template: this.promptSystemName,
          prompt_template_variant: this.selectedRowDetails?.variant,
        })) || undefined

      this.text = this.detailedResponse?.['content'] ?? ''
      this.loading = false
    },

    async handleFilesUpload(files) {
      if (!files || files.length === 0) {
        this.testText = ''
        return
      }

      try {
        this.fileUploadInProgress = true
        const parsedTexts = await Promise.all(
          files.map(async (file) => {
            const content = await this.parsePdf(file)
            const contentString = content.pages.join('\n')

            return `# File: ${file.name}\n\n${contentString}`
          })
        )
        this.testText = parsedTexts.join('\n\n')
      } catch (error) {
        console.error('Error parsing files:', error)
      }

      this.fileUploadInProgress = false
    },

    async parsePdf(file) {
      console.log('parsePdf', file)
      const endpoint = this.store.getters.config.api.aiBridge.urlAdmin
      const formData = new FormData()

      if (!file) {
        throw Error('File is mising')
      }

      formData.append('file', file)

      return await fetchData({
        method: 'POST',
        endpoint,
        credentials: 'include',
        service: `utils/parse-pdf`,
        body: formData,
        headers: {},
      })
        .then((response) => {
          if (response.ok) return response.json()
          if (response.error) throw response
        })
        .then((pdfContent) => {
          return pdfContent
        })
        .catch((response) => {
          throw {
            technicalError: response?.error,
            text: `Error parsing PDF file`,
          }
        })
    },
  },
})
</script>
