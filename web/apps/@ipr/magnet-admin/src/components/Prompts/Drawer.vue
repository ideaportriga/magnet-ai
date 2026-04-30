<template>
  <km-drawer-layout storage-key="drawer-prompts" no-scroll>
    <div class="stack full-height full-width min-h-0 min-w-0" data-gap="md">
      <div class="cluster km-heading-7" data-align="center" data-gap="sm" data-justify="between" data-wrap="no">
        <div>{{ m.common_preview() }}</div>
        <km-btn flat simple :label="m.common_evaluate()" icon-size="16px" icon="clipboard-check" @click="showNewDialog = true" />
      </div>
      <div class="stack flex-none min-w-0 overflow-auto" data-gap="sm">
        <div class="stack" data-gap="sm">
          <div class="stack" data-gap="xs">
            <div class="cluster" data-align="center" data-gap="sm" data-justify="between" data-wrap="no">
              <div class="flex-1">
                <div class="km-title text-secondary-text">{{ m.common_input() }}</div>
              </div>
              <div class="flex-none">
                <km-btn flat round dense icon="code" :tone="inputViewMode === 'code' ? 'brand' : 'weak'" :tooltip="m.prompts_showRawInput()" @click="inputViewMode = 'code'" />
                <km-btn flat round dense icon="eye" :tone="inputViewMode === 'preview' ? 'brand' : 'weak'" :tooltip="m.prompts_showRenderedPreview()" @click="inputViewMode = 'preview'" />
              </div>
            </div>
            <div v-show="inputViewMode === 'preview'" class="bg-light rounded-lg p-sm overflow-auto">
              <km-markdown :source="testText" />
            </div>
            <km-input v-show="inputViewMode === 'code'" ref="input" data-test="preview-input" autogrow :rows="1" :min-rows="1" :max-rows="10" :placeholder="m.prompts_typeYourText()" :model-value="testText" type="textarea" @input="testText = $event" @keydown.enter="submit">
              <template #append>
                <km-btn data-test="preview-btn" type="button" size="icon-xs" icon="send" icon-size="16px" icon-tone="inverse" :disable="!testText?.length" @click="submit" />
              </template>
            </km-input>
            <div class="km-field text-secondary-text">{{ m.prompts_plainTextOrJson() }}</div>
          </div>
          <div class="cluster full-width" data-align="center" data-gap="sm" data-justify="between" data-wrap="no">
            <km-select-flat :placeholder="m.prompts_inputOptions()" :options="inputOptions" :model-value="selectedInputOptionOption" @update:model-value="onInputOptionSelect" />
          </div>
        </div>
        <km-file-picker v-if="selectedInputOption === &quot;pdf&quot;" :model-value="files" accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.odt,.ods,.rtf,.html,.htm,.csv,.tsv,.txt,.md,.eml,.epub,.png,.jpg,.jpeg,.gif,.webp,.bmp,.tiff" multiple :loading="fileUploadInProgress" :hint="m.prompts_dropFiles()" @update:model-value="onFilePickerUpdate" />
        <div v-if="selectedInputOption === &quot;audio&quot;" class="stack" data-gap="xs">
          <km-file-picker :model-value="audioFiles" accept=".flac,.m4a,.mp3,.ogg,.wav,.webm,.mp4" :loading="audioUpload.isUploading.value" :loading-text="audioUpload.uploadStatus.value" :hint="m.prompts_dropAudioFile()" @update:model-value="onAudioFilePickerUpdate" />
          <div v-if="audioUpload.error.value">
            <div class="flex-1 text-negative text-body2">{{ audioUpload.error.value }}</div>
          </div>
        </div>
        <div v-if="selectedInputOption === &quot;speech&quot;" class="stack" data-gap="xs">
          <div class="cluster" data-align="center" data-gap="sm">
            <div class="flex-none">
              <km-btn v-if="!scribe.isConnected.value" outline tone="brand" size="sm" padding="6px 12px" @click="startTranscription">
                <km-glyph class="mr-xs" name="microphone" size="14px" />{{ m.prompts_startRecording() }}
              </km-btn>
              <km-btn v-else outline tone="danger" size="sm" padding="6px 12px" @click="stopTranscription">
                <km-glyph class="mr-xs" name="stop" size="14px" />{{ m.prompts_stopRecording() }}
              </km-btn>
            </div>
            <div v-if="isLoadingToken || scribe.isConnected.value" class="flex-1">
              <km-loader v-if="isLoadingToken" size="20px" /><span v-else-if="scribe.isConnected.value" class="text-error-text"><span class="mr-xs">●</span>{{ m.prompts_recording() }}</span>
            </div>
          </div>
          <div v-if="scribe.error.value">
            <div class="flex-1 text-negative text-body2">{{ scribe.error.value }}</div>
          </div>
        </div>
        <div class="stack flex-none" data-gap="sm">
          <km-separator class="my-0" />
          <div class="cluster min-w-0" data-align="center" data-gap="sm" data-justify="between" data-wrap="no">
            <div class="flex-1">
              <div class="km-title text-secondary-text">{{ m.common_output() }}</div>
            </div>
            <div class="cluster" data-gap="xs" data-justify="end" data-wrap="no">
              <km-btn v-if="detailedResponse" tone="brand" icon-tone="brand" interaction-tone="brand" label-class="km-title" :label="m.common_viewCostsLatency()" flat icon-size="16px" @click="showDetails = true" />
              <km-toggle v-model="markdown" :label="m.common_markdown()" />
            </div>
          </div>
        </div>
      </div>
      <km-scroll-area class="flex-1 min-h-0">
        <template v-if="loading">
          <div class="cluster" data-justify="center">
            <km-loader size="62px" />
          </div>
        </template>
        <template v-else-if="text !== undefined">
          <div class="cluster pt-sm" data-wrap="no">
            <div class="flex-none">
              <km-avatar tone="brand" size="36px">
                <km-icon :name="&quot;magnet&quot;" width="20" height="22" />
              </km-avatar>
            </div>
            <div class="flex-1 rounded-lg pb-md">
              <div class="p-sm">
                <km-markdown v-if="markdown" :source="text" />
                <pre v-if="!markdown" class="font-mono whitespace-pre-wrap overflow-auto">{{ text }}</pre>
              </div>
            </div>
          </div>
        </template>
      </km-scroll-area>
    </div>
    <template #footer>
      <div class="cluster" data-align="center" data-gap="sm" data-justify="between" data-wrap="no">
        <km-btn flat simple :label="m.common_clearPreview()" icon-size="16px" icon="eraser" @click="clearText" />
        <km-btn icon="copy" icon-size="16px" size="sm" flat :label="m.common_copy()" :tooltip="m.common_copy()" @click="copy" />
      </div>
    </template>
    <evaluation-jobs-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" :system_name="promptSystemName" type="prompt_template" disable-prompt-selection @create="createEvaluation" @cancel="showNewDialog = false" />
    <km-popup-confirm :visible="showEvaluationCreateDialog" :confirm-button-label="m.common_viewEvaluation()" notification-icon="check" :cancel-button-label="m.common_cancel()" @cancel="showEvaluationCreateDialog = false" @confirm="navigateToEval()">
      <div class="cluster km-heading-7" data-justify="center">{{ m.common_evaluationStarted() }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.common_evaluationTakeTime() }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.common_evaluationViewResults() }}</div>
    </km-popup-confirm>
    <km-popup-confirm :visible="showDetails" :title="m.prompts_costsAndLatency()" :confirm-button-label="m.common_ok()" :cancel-button-label="m.common_cancel()" @cancel="showDetails = false" @confirm="showDetails = false">
      <prompts-cost-popup :record="detailedResponse" />
    </km-popup-confirm>
  </km-drawer-layout>
</template>
<script>
import { defineComponent, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { copyToClipboard } from '@ds/utils/clipboard'
import { useAppStore } from '@/stores/appStore'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { useSpecificationsStore } from '@/stores/specificationsStore'
import { fetchData } from '@shared'
import { useScribe } from '@/composables/useScribe'
import { useAudioUpload } from '@/composables/useAudioUpload'
import { notify } from '@shared/utils/notify'

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
        { label: m.prompts_manualInput(), value: null },
        { label: m.prompts_documentUpload(), value: 'pdf' },
        { label: m.prompts_audioUpload(), value: 'audio' },
        { label: m.prompts_speechToText(), value: 'speech' },
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
      notify.success(m.prompts_outputCopied())
    },
    clearText() {
      this.text = undefined
    },

    async submit(event) {
      if (event?.shiftKey) return
      event?.preventDefault?.()

      const selectedModel = this.selectedRowDetails?.system_name_for_model
      if (!selectedModel) {
        notify.error(`${m.common_llmModel()}: ${m.common_required()}`)
        return
      }

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
          system_name_for_model: selectedModel,
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
         throw Error(m.prompts_fileMissing())
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
             text: m.prompts_errorParsingPdf(),
           }
        })
    },
  },
})
</script>
