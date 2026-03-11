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
      .row.q-mt-sm.items-center
        .col-auto
          km-select-flat(
            placeholder='Input Options',
            :options='inputOptions',
            :model-value='selectedInputOptionOption',
            @update:model-value='onInputOptionSelect'
          )
      template(v-if='selectedInputOption === "pdf"')
        .q-mt-md
          km-file-picker(
            :model-value='files',
            accept='.pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.odt,.ods,.rtf,.html,.htm,.csv,.tsv,.txt,.md,.eml,.epub,.png,.jpg,.jpeg,.gif,.webp,.bmp,.tiff',
            multiple,
            :loading='fileUploadInProgress',
            hint='Drop files or click to browse (PDF, Word, Excel, PowerPoint, images, etc.)',
            @update:model-value='onFilePickerUpdate'
          )
      template(v-if='selectedInputOption === "audio"')
        .q-mt-md
          km-file-picker(
            :model-value='audioFiles',
            accept='.flac,.m4a,.mp3,.ogg,.wav,.webm,.mp4',
            :loading='audioUpload.isUploading.value',
            :loading-text='audioUpload.uploadStatus.value',
            hint='Drop audio file or click to browse',
            @update:model-value='onAudioFilePickerUpdate'
          )
          .row(v-if='audioUpload.error.value').q-mt-xs
            .col.text-negative.text-body2 {{ audioUpload.error.value }}
      template(v-if='selectedInputOption === "speech"')
        .q-mt-md
          .row.items-center
            .col-auto.q-mr-sm
              q-btn(
                v-if='!scribe.isConnected.value',
                outline,
                color='primary',
                @click='startTranscription',
                size='sm',
                padding='6px 12px'
              )
                q-icon(name='fas fa-microphone', size='14px', class='q-mr-xs')
                | Start recording
              q-btn(
                v-else,
                outline,
                color='error-text',
                @click='stopTranscription',
                size='sm',
                padding='6px 12px'
              )
                q-icon(name='fas fa-stop', size='14px', class='q-mr-xs')
                | Stop recording
            .col(v-if='isLoadingToken || scribe.isConnected.value')
              q-spinner(v-if='isLoadingToken', size='20px', color='primary')
              span(v-else-if='scribe.isConnected.value').text-error-text
                span.q-mr-xs ●
                | Recording…
          .row(v-if='scribe.error.value').q-mt-xs
            .col.text-negative.text-body2 {{ scribe.error.value }}
      .q-mt-md

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
    type='prompt_template',
    disable-prompt-selection
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
import { useScribe } from '@/composables/useScribe'
import { useAudioUpload } from '@/composables/useAudioUpload'

export default defineComponent({
  props: ['open'],
  emits: ['update:open'],
  setup() {
    const store = useStore()
    const scribe = useScribe({ modelId: 'scribe_v2_realtime' })
    const audioUpload = useAudioUpload({
      endpoint: () => store.getters.config?.api?.aiBridge?.urlAdmin ?? '',
      credentials: 'include',
      language: 'en',
    })
    const isLoadingToken = ref(false)
    const transcriptionBaseText = ref('')
    const selectedInputOption = ref(null)

    return {
      store,
      scribe,
      audioUpload,
      isLoadingToken,
      transcriptionBaseText,
      selectedInputOption,
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
      audioFiles: ref([]),
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
    inputOptions() {
      return [
        { label: 'Manual input', value: null },
        { label: 'Document upload', value: 'pdf' },
        { label: 'Audio upload', value: 'audio' },
        { label: 'Speech to Text', value: 'speech' },
      ]
    },
    selectedInputOptionOption() {
      if (!this.selectedInputOption) return null
      return this.inputOptions.find((o) => o.value === this.selectedInputOption) ?? null
    },
    scribeCommitted() {
      return this.scribe.committedTranscripts?.value ?? []
    },
    scribePartial() {
      return this.scribe.partialTranscript?.value ?? ''
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
    open(newVal) {
      if (!newVal && this.scribe.isConnected.value) {
        this.scribe.pause()
        this.testText = this.buildTranscriptString()
        this.scribe.disconnect()
        this.scribe.error.value = null
      }
    },
    scribeCommitted: {
      handler() {
        if (this.scribe.isConnected.value) {
          this.testText = this.buildTranscriptString()
        }
      },
      deep: true,
    },
    scribePartial() {
      if (this.scribe.isConnected.value) {
        this.testText = this.buildTranscriptString()
      }
    },
  },
  methods: {
    buildTranscriptString() {
      const parts = this.scribe.committedTranscripts.value.map((t) => t.text)
      const partial = this.scribe.partialTranscript.value?.trim()
      if (partial) parts.push(partial)
      const suffix = parts.join('\n\n').trim()
      const base = this.transcriptionBaseText?.trim() ?? ''
      return base ? (suffix ? `${base}\n\n${suffix}` : base) : suffix
    },
    async getScribeToken() {
      const endpoint = this.store.getters.config.api.aiBridge.urlAdmin
      const response = await fetchData({
        method: 'GET',
        endpoint,
        credentials: 'include',
        service: 'recordings/scribe-token',
      })
      if (response.error) throw response.error
      const data = await response.json()
      return data?.token ?? data?.key ?? data
    },
    async startTranscription() {
      this.scribe.error.value = null
      this.isLoadingToken = true
      try {
        const token = await this.getScribeToken()
        this.transcriptionBaseText = this.testText || ''
        await this.scribe.connect({
          token,
          microphone: { echoCancellation: true, noiseSuppression: true },
        })
      } catch (e) {
        const msg = e?.response?.data?.detail ?? e?.message ?? e?.detail ?? String(e)
        this.scribe.error.value = msg
      } finally {
        this.isLoadingToken = false
      }
    },
    stopTranscription() {
      this.scribe.pause()
      this.testText = this.buildTranscriptString()
      this.scribe.disconnect()
      // this.selectedInputOption = null
    },
    onInputOptionSelect(option) {
      this.selectedInputOption = option?.value ?? null
    },
    onFilePickerUpdate(value) {
      this.files = value
      const arr = Array.isArray(value) ? value : value ? [value] : []
      this.handleFilesUpload(arr)
    },
    async onAudioFilePickerUpdate(value) {
      const file = Array.isArray(value) ? value?.[0] : value
      if (!file) {
        this.audioFiles = []
        this.audioUpload.reset()
        return
      }
      this.audioFiles = [file]
      this.audioUpload.reset()
      try {
        const { segments } = await this.audioUpload.uploadAndTranscribe(file)
        this.testText = JSON.stringify(segments, null, 2)
        this.audioFiles = []
        this.selectedInputOption = null
      } catch {
        // error shown via audioUpload.error
      }
    },
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
      this.selectedInputOption = null

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
      this.selectedInputOption = null
      this.files = []
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
