<template lang="pug">
km-drawer-layout(storageKey="drawer-prompts", noScroll)
  template(#header)
    .km-heading-7
      .row
        .col {{ m.common_preview() }}
        .col-auto
          km-btn(flat, simple, :label='m.common_evaluate()', iconSize='16px', icon='fas fa-clipboard-check', @click='showNewDialog = true')
  .column.full-height.full-width.no-wrap.q-px-16
    .col-auto(style='overflow-x: auto')
      .row.items-center.q-mb-xs
        .col
          .km-heading-5.text-text-grey {{ m.common_input() }}
        .col-auto
          q-btn(
            flat,
            round,
            dense,
            icon='code',
            :color="inputViewMode === 'code' ? 'primary' : 'grey-5'",
            @click="inputViewMode = 'code'"
          )
            q-tooltip.bg-white.block-shadow.km-description.text-text-grey Show raw input
          q-btn(
            flat,
            round,
            dense,
            icon='visibility',
            :color="inputViewMode === 'preview' ? 'primary' : 'grey-5'",
            @click="inputViewMode = 'preview'"
          )
            q-tooltip.bg-white.block-shadow.km-description.text-text-grey Show rendered preview

      div.prompt-locked.markdown-content(v-show="inputViewMode === 'preview'")
        div(v-html='inputRenderedHtml')
      km-input(
        v-show="inputViewMode === 'code'",
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
              :label='m.common_viewCostsLatency()',
              @click='showDetails = true',
              flat,
              iconSize='16px',
              hoverBg='primary-bg'
            )
          .col-auto
            q-toggle(v-model='markdown', :label='m.common_markdown()', color='primary')
    q-scroll-area.col(style='min-height: 0')
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
          km-btn(flat, simple, :label='m.common_clearPreview()', iconSize='16px', icon='fas fa-eraser', @click='clearText')
        q-space
        .col-auto
          km-btn(icon='fas fa-copy', iconSize='16px', size='sm', flat, @click='copy', :label='m.common_copy()', tooltip='Copy')

  evaluation-jobs-create-new(
    :showNewDialog='showNewDialog',
    @create='createEvaluation',
    @cancel='showNewDialog = false',
    v-if='showNewDialog',
    :system_name='promptSystemName',
    type='prompt_template',
    disable-prompt-selection
  )
  km-popup-confirm(
    :visible='showEvaluationCreateDialog',
    confirmButtonLabel='View Evaluation',
    notificationIcon='far fa-circle-check',
    :cancelButtonLabel='m.common_cancel()',
    @cancel='showEvaluationCreateDialog = false',
    @confirm='navigateToEval()'
  )
    .row.item-center.justify-center.km-heading-7 Evaluation has started!
    .row.text-center.justify-center It may take some time for the Evaluation to finish.
    .row.text-center.justify-center You'll be able to view run results on the Evaluation screen.
  km-popup-confirm(
    :visible='showDetails',
    title='Costs & Latency',
    confirmButtonLabel='OK',
    :cancelButtonLabel='m.common_cancel()',
    @cancel='showDetails = false',
    @confirm='showDetails = false'
  )
    prompts-cost-popup(:record='detailedResponse')
</template>
<script>
import { defineComponent, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { copyToClipboard } from 'quasar'
import { useAppStore } from '@/stores/appStore'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { useSpecificationsStore } from '@/stores/specificationsStore'
import { fetchData } from '@shared'
import { useScribe } from '@/composables/useScribe'
import { useAudioUpload } from '@/composables/useAudioUpload'
import MarkdownIt from 'markdown-it'

export default defineComponent({
  props: ['open'],
  emits: ['update:open'],
  setup() {
    const { draft, activeVariant, testSetItem } = useVariantEntityDetail('promptTemplates')
    const appStore = useAppStore()
    const specsStore = useSpecificationsStore()
    const scribe = useScribe({ modelId: 'scribe_v2_realtime' })
    const audioUpload = useAudioUpload({
      endpoint: () => appStore.config?.api?.aiBridge?.urlAdmin ?? '',
      credentials: 'include',
      language: 'en',
    })
    const isLoadingToken = ref(false)
    const transcriptionBaseText = ref('')
    const selectedInputOption = ref(null)
    const md = new MarkdownIt({ html: false, breaks: true })

    return {
      m,
      draft,
      activeVariant,
      testSetItem,
      appStore,
      specsStore,
      scribe,
      audioUpload,
      isLoadingToken,
      transcriptionBaseText,
      selectedInputOption,
      markdownRenderer: md,
      inputViewMode: ref('code'),
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
      return this.draft
    },
    selectedRowDetails() {
      return { name: this.draft?.name, ...this.activeVariant }
    },
    promptSystemName() {
      return this.selectedRow?.system_name
    },
    promptTemplateTestSetItem() {
      return this.testSetItem
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
    inputRenderedHtml() {
      const input = this.testText || ''
      const varRegex = /\{[A-Za-z_][A-Za-z0-9_]*\}/g
      const vars = []
      const textForMd = input.replace(varRegex, (match) => {
        const varName = match.slice(1, -1)
        const idx = vars.length
        vars.push(varName)
        return `\u200B__VAR${idx}__\u200B`
      })
      let html = this.markdownRenderer.render(textForMd)
      vars.forEach((varName, idx) => {
        const placeholder = `\u200B__VAR${idx}__\u200B`
        const escaped = varName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
        html = html.split(placeholder).join(`<span class="prompt-var-chip">${escaped}</span>`)
      })
      return html
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
      const endpoint = this.appStore.config.api.aiBridge.urlAdmin
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
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Output has been copied to clipboard', timeout: 1000 })
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
        (await this.specsStore.enhanceTextDetails({
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

      }
      this.selectedInputOption = null
      this.files = []
      this.fileUploadInProgress = false
    },

    async parsePdf(file) {

      const endpoint = this.appStore.config.api.aiBridge.urlAdmin
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

<style lang="stylus" scoped>
.prompt-locked
  background: #f7f7f9
  border-radius: 8px
  padding: 12px 16px
  min-height: 120px
  max-height: 220px
  overflow-y: auto
  font-size: var(--km-font-size-caption)

.prompt-locked :deep(.prompt-var-chip)
  display: inline-flex
  align-items: center
  padding: 2px 8px
  margin: 2px 2px
  border-radius: 4px
  font-size: var(--km-font-size-caption)
  font-weight: 500
  border: 1px solid var(--q-primary)
  color: var(--q-primary)
  background: transparent

.prompt-locked :deep(p)
  margin: 0 0 8px 0
  line-height: 1.5

.prompt-locked :deep(p:last-child)
  margin-bottom: 0

.prompt-locked :deep(ul),
.prompt-locked :deep(ol)
  padding-left: 20px
  margin: 0 0 8px 0

.prompt-locked :deep(table)
  border-collapse: collapse
  border: 1px solid rgba(0, 0, 0, 0.12)
  margin: 0 0 8px 0
  width: auto
  font-size: inherit

.prompt-locked :deep(th),
.prompt-locked :deep(td)
  border: 1px solid rgba(0, 0, 0, 0.12)
  padding: 6px 10px
  text-align: left
  font-size: inherit

.prompt-locked :deep(pre),
.prompt-locked :deep(code)
  background: rgba(0, 0, 0, 0.06)
  border-radius: 4px
  padding: 2px 6px
  font-size: var(--km-font-size-caption)

.prompt-locked :deep(pre)
  padding: 12px
  overflow-x: auto
  white-space: pre-wrap

.prompt-locked :deep(h1),
.prompt-locked :deep(h2),
.prompt-locked :deep(h3),
.prompt-locked :deep(h4),
.prompt-locked :deep(h5),
.prompt-locked :deep(h6)
  margin: 12px 0 6px 0
  line-height: 1.3
  font-size: var(--km-font-size-h2)
  font-weight: 600

.prompt-locked :deep(h2)
  font-size: var(--km-font-size-body-lg)

.prompt-locked :deep(h3)
  font-size: 15px

.prompt-locked :deep(h4)
  font-size: var(--km-font-size-body)

.prompt-locked :deep(h5)
  font-size: var(--km-font-size-label)

.prompt-locked :deep(h6)
  font-size: var(--km-font-size-caption)

.prompt-locked :deep(h1:first-child),
.prompt-locked :deep(h2:first-child),
.prompt-locked :deep(h3:first-child),
.prompt-locked :deep(h4:first-child)
  margin-top: 0

.prompt-locked :deep(strong)
  font-weight: 600

.prompt-locked :deep(a)
  color: var(--q-primary)
  text-decoration: none

.prompt-locked :deep(a:hover)
  text-decoration: underline
</style>
