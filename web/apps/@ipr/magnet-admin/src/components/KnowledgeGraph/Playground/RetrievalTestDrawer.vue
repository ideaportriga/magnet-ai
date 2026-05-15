<template>
  <km-drawer-layout storage-key="drawer-kg-retrieval" :default-width="420" :min-width="360" :max-width="800" no-scroll>
    <template #header>
      <div class="header-content">
        <div class="header-title">
          <div class="km-heading-7">{{ m.knowledgeGraph_testRetrieval() }}</div>
          <div class="km-description text-secondary-text">{{ m.knowledgeGraph_askQuestionsAboutKB() }}</div>
        </div>
        <div class="header-actions">
          <km-btn v-if="messages.length > 0" flat icon="redo" icon-size="14px" size="sm" :label="m.panel_clearChat()" @click="clearChat" />
          <km-btn flat round dense icon="close" size="sm" @click="$emit('close')" />
        </div>
      </div>
    </template>

    <!-- Messages Area -->
    <div ref="messagesContainer" class="messages-area">
      <!-- Empty State -->
      <div v-if="messages.length === 0 && !processing" class="empty-state">
        <km-glyph name="chats" size="48px" tone="muted" />
        <div class="km-heading-6 mt-md text-secondary-text">{{ m.knowledgeGraph_startConversation() }}</div>
        <div class="km-description text-grey-6 mt-xs">{{ m.knowledgeGraph_askQuestionsToTest() }}</div>
      </div>

      <!-- Messages List -->
      <div v-else class="messages-list">
        <template v-for="msg in messages" :key="msg.id">
          <!-- User Message -->
          <div v-if="msg.role === 'user'" class="message-row user-message">
            <div class="message-content-wrapper">
              <div class="message-bubble user-bubble">
                <div class="km-paragraph">{{ msg.content }}</div>
              </div>
              <div class="message-meta">
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
            </div>
          </div>

          <!-- Assistant Message -->
          <div v-else-if="msg.role === 'assistant'" class="message-row assistant-message">
            <div class="message-content-wrapper">
              <div class="message-bubble assistant-bubble">
                <!-- Workflow Section (Tool Calling Chain) -->
                <div v-if="msg.workflow && msg.workflow.length > 0" class="workflow-section">
                  <div class="workflow-toggle" @click="msg.workflowExpanded = !msg.workflowExpanded">
                    <km-glyph name="graph" size="14px" tone="accent" />
                    <span class="km-field text-teal-7">{{ m.knowledgeGraph_executionFlow() }}</span>
                    <km-glyph :name="msg.workflowExpanded ? 'chevron-up' : 'chevron-down'" size="12px" tone="accent" />
                  </div>

                  <km-slide-transition>
                    <div v-show="msg.workflowExpanded" class="workflow-timeline">
                      <div
                        v-for="(step, idx) in msg.workflow"
                        :key="idx"
                        class="workflow-step"
                        :class="{ 'workflow-step--last': idx === msg.workflow.length - 1 }"
                      >
                        <div class="workflow-step-marker">
                          <div class="workflow-step-icon-circle" :class="getToolDotClass(step.tool)">
                            <km-glyph :name="getToolIcon(step.tool)" size="14px" tone="inverse" />
                          </div>
                          <div class="workflow-step-line" />
                        </div>
                        <div class="workflow-step-content">
                          <div class="workflow-step-header cursor-pointer" @click="step.expanded = !step.expanded">
                            <div class="cluster" data-justify="between">
                              <span class="workflow-step-tool">{{ formatToolName(step.tool) }}</span>
                              <km-glyph :name="step.expanded ? 'chevron-up' : 'chevron-down'" size="10px" tone="muted" />
                            </div>
                            <div style="font-size: 12px; font-weight: 400">
                              <span class="text-grey-6">Step {{ step.iteration }}</span>
                              <span v-if="step.call_summary?.result_count" class="text-grey-6 ml-xs">•</span>
                              <span v-if="typeof step.call_summary?.result_count === 'number'" class="text-green-8">
                                Found {{ step.call_summary?.result_count }} record{{ step.call_summary?.result_count > 1 ? 's' : '' }}
                              </span>
                            </div>
                          </div>
                          <km-slide-transition>
                            <div v-show="step.expanded">
                              <div v-if="Object.keys(step.arguments || {}).length > 0" class="workflow-step-args">
                                <div class="workflow-args-label">{{ m.knowledgeGraph_argumentsLabel() }}</div>
                                <div v-for="(value, key) in step.arguments" :key="key" class="workflow-arg">
                                  <span class="workflow-arg-key">{{ key }}:</span>
                                  <span class="text-grey-9" style="font-size: 12px">{{ formatArgValue(value) }}</span>
                                </div>
                              </div>
                              <div v-if="step.call_summary.reasoning" class="workflow-step-args">
                                <div class="workflow-args-label">{{ m.knowledgeGraph_reasoningLabel() }}</div>
                                <div class="text-grey-9" style="font-size: 12px">{{ step.call_summary?.reasoning }}</div>
                              </div>
                            </div>
                          </km-slide-transition>
                        </div>
                      </div>
                    </div>
                  </km-slide-transition>
                </div>

                <!-- Response Content -->
                <div v-if="msg.content" class="response-content">
                  <RetrievalResponseContent :content="msg.content" :format="props.outputFormat" />
                </div>

                <!-- Streaming indicator -->
                <div v-else-if="msg.streaming" class="streaming-dots">
                  <span class="dot" />
                  <span class="dot" />
                  <span class="dot" />
                </div>

                <!-- Empty content state (no text response) -->
                <div v-else class="empty-response">
                  <div class="empty-response-text">
                    <span class="km-description text-grey-6">{{ m.knowledgeGraph_noTextResponse() }}</span>
                  </div>
                </div>

                <!-- Sources Section -->
                <div v-if="msg.sources && msg.sources.length > 0" class="sources-section">
                  <div class="sources-header" @click="msg.sourcesExpanded = !msg.sourcesExpanded">
                    <km-glyph name="attach" size="11px" tone="weak" />
                    <span class="sources-label">{{ msg.sources.length }} source{{ msg.sources.length > 1 ? 's' : '' }}</span>
                    <km-glyph :name="msg.sourcesExpanded ? 'chevron-up' : 'chevron-down'" size="10px" tone="muted" />
                  </div>

                  <km-slide-transition>
                    <div v-show="msg.sourcesExpanded" class="sources-list">
                      <div v-for="group in groupSourcesByDocument(msg.sources)" :key="group.document_id" class="source-document-group">
                        <router-link
                          :to="{ name: 'KnowledgeGraphDocumentDetail', params: { id: graphId, documentId: group.document_id } }"
                          class="source-document-group-header"
                          target="_blank"
                          rel="noopener"
                          @click.stop
                        >
                          <km-glyph name="file-text" size="12px" tone="weak" />
                          <span class="source-document-group-title">{{ truncate(group.document_name, 35) }}</span>
                          <km-glyph name="external-link" size="10px" tone="muted" class="source-document-link-icon" />
                        </router-link>
                        <div class="source-document-chunks">
                          <div v-for="(source, idx) in group.sources" :key="idx" class="source-chip" @click="openSourceDetail(source)">
                            <span class="source-chip-num">{{ source.globalIndex }}</span>
                            <span class="source-chip-title">{{ truncate(source.chunk_title || 'Untitled', 40) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </km-slide-transition>
                </div>
              </div>
              <div class="message-meta">
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Processing Indicator -->
        <div v-if="processing" class="message-row assistant-message">
          <div class="message-content-wrapper">
            <div class="message-bubble assistant-bubble processing-bubble">
              <km-loader size="24px" />
              <span class="km-description text-secondary-text ml-sm">{{ m.knowledgeGraph_thinking() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <form class="input-form" @submit.prevent="sendMessage">
        <km-input
          ref="inputRef"
          v-model="userInput"
          data-test="preview-input"
          :placeholder="m.knowledgeGraph_askQuestion()"
          autogrow
          border-radius="8px"
          class="message-input"
          @keydown.enter="handleEnter"
        />
        <km-btn data-test="preview-btn" type="submit" unelevated round :disable="!canSend" :loading="processing" padding="8px" class="send-btn">
          <km-glyph name="send" size="14px" />
        </km-btn>
      </form>
    </div>

    <!-- Source Detail Dialog -->
    <km-dialog v-model="showSourceDialog" position="right" maximized>
      <km-card class="source-dialog-card">
        <div class="km-card-section source-dialog-header">
          <div class="cluster" data-wrap="no" data-align="start">
            <div class="flex-1">
              <div class="cluster" data-wrap="no">
                <router-link
                  v-if="selectedDocumentRoute"
                  :to="selectedDocumentRoute"
                  class="km-heading-7 source-document-link"
                  target="_blank"
                  rel="noopener"
                >
                  {{ selectedSource?.document_title || selectedSource?.document_name || 'Document' }}
                </router-link>
                <div v-else class="km-heading-7">
                  {{ selectedSource?.document_title || selectedSource?.document_name || 'Document' }}
                </div>
              </div>
              <div class="km-heading-8">{{ selectedSource?.chunk_title || 'Source Content' }}</div>
            </div>
            <km-btn flat round dense icon="close" @click="showSourceDialog = false" />
          </div>
        </div>
        <km-separator />
        <div class="km-card-section source-dialog-content">
          <RetrievalResponseContent :content="selectedSource?.chunk_content || ''" class="source-full-text" />
        </div>
      </km-card>
    </km-dialog>
  </km-drawer-layout>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { tools } from '../Retrieval/models'
import RetrievalResponseContent from './RetrievalResponseContent.vue'

interface WorkflowStep {
  iteration: number
  tool: string
  arguments: Record<string, any>
  call_summary: Record<string, any>
  expanded?: boolean
}

interface Source {
  document_id?: string
  document_name?: string
  document_title?: string
  chunk_title: string
  chunk_content: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content?: string
  timestamp: Date
  sources?: Source[]
  sourcesExpanded?: boolean
  workflow?: WorkflowStep[]
  workflowExpanded?: boolean
  streaming?: boolean
}

const props = withDefaults(
  defineProps<{
    graphId: string
    outputFormat?: 'plain' | 'markdown'
    isActive?: boolean
  }>(),
  {
    outputFormat: 'markdown',
    isActive: false,
  }
)

defineEmits<{
  close: []
}>()

const appStore = useAppStore()

// State
const userInput = ref('')
const messages = ref<Message[]>([])
const processing = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<any>(null)
const conversationId = ref<string | null>(null)

// Source dialog state
const showSourceDialog = ref(false)
const selectedSource = ref<Source | null>(null)
const selectedDocumentRoute = computed(() => {
  const docId = selectedSource.value?.document_id
  if (!docId) return null
  return `/knowledge-graph/${props.graphId}/documents/${docId}`
})

// Computed
const canSend = computed(() => userInput.value.trim().length > 0 && !processing.value)

// Methods
const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const truncate = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  e.preventDefault()
  sendMessage()
}

// Workflow display helpers
const getToolIcon = (tool: string): string => {
  const icons: Record<string, string> = {
    findChunksBySimilarity: 'search',
    findDocumentsBySummarySimilarity: 'filter_alt',
    findDocumentsByMetadata: 'tags',
    findDocumentsByEntitySimilarity: 'graph',
    exit: 'sign-out',
  }
  return icons[tool] || 'settings'
}

const getToolDotClass = (tool: string): string => {
  return `workflow-step-dot--${tools.find((t) => t.name === tool)?.ui?.previewExecutionFlowColor || 'grey'}`
}

const formatToolName = (tool: string): string => {
  return tools.find((t) => t.name === tool)?.label || tool.replace(/([A-Z])/g, ' $1').trim()
}

const formatArgValue = (value: any): string => {
  if (typeof value === 'string') {
    return value
  }
  if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
    try {
      return JSON.stringify(value)
    } catch (error) {
      return String(value)
    }
  }
  return String(value)
}

// Source detail
const openSourceDetail = (source: Source) => {
  selectedSource.value = source
  showSourceDialog.value = true
}

interface SourceWithIndex extends Source {
  globalIndex: number
}

interface DocumentGroup {
  document_id: string
  document_name: string
  sources: SourceWithIndex[]
}

const groupSourcesByDocument = (sources: Source[]): DocumentGroup[] => {
  const groups = new Map<string, DocumentGroup>()
  sources.forEach((source, idx) => {
    const docId = source.document_id || 'unknown'
    if (!groups.has(docId)) {
      groups.set(docId, {
        document_id: docId,
        document_name: source.document_title || source.document_name || 'Unknown Document',
        sources: [],
      })
    }
    groups.get(docId)!.sources.push({ ...source, globalIndex: idx + 1 })
  })
  return Array.from(groups.values())
}

const sendMessage = async () => {
  if (!canSend.value) return

  const userMessage: Message = {
    id: generateId(),
    role: 'user',
    content: userInput.value.trim(),
    timestamp: new Date(),
  }
  messages.value.push(userMessage)
  userInput.value = ''
  processing.value = true
  await scrollToBottom()

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const requestBody: Record<string, any> = { query: userMessage.content }

    // Include conversation_id if we have one (for multi-turn conversation)
    if (conversationId.value) {
      requestBody.conversation_id = conversationId.value
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/retrieval/preview`,
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })

    if (response.ok) {
      const data = await response.json()

      // Store conversation_id for subsequent requests
      if (data?.conversation_id) {
        conversationId.value = data.conversation_id
      }

      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: data?.content || '',
        timestamp: new Date(),
        sources: Array.isArray(data?.sources) ? data.sources : [],
        sourcesExpanded: false,
        workflow: Array.isArray(data?.workflow) ? data.workflow.map((step: any) => ({ ...step, expanded: false })) : [],
        workflowExpanded: false,
      }
      messages.value.push(assistantMessage)
    } else {
      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: m.knowledgeGraph_retrievalFailed(),
        timestamp: new Date(),
      }
      messages.value.push(assistantMessage)
    }
  } catch (err) {
    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: m.knowledgeGraph_retrievalError(),
      timestamp: new Date(),
    }
    messages.value.push(assistantMessage)
  }

  processing.value = false
  await scrollToBottom()
}

const clearChat = () => {
  messages.value = []
  conversationId.value = null // Reset conversation when clearing chat
}

watch(
  () => props.graphId,
  () => {
    clearChat()
  }
)

watch(
  () => props.isActive,
  (active) => {
    if (active) {
      nextTick(() => {
        inputRef.value?.focus()
        scrollToBottom()
      })
    }
  }
)

onMounted(() => {
  inputRef.value?.focus()
})
</script>

<style scoped>
/* Header */
.drawer-header {
  flex-shrink: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Messages Area */
.messages-area {
  flex: 1;
  overflow-block: auto;
  padding: 16px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  block-size: 100%;
  text-align: center;
  padding: 40px 20px;
}

/* Messages List */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Message Row */
.message-row {
  display: flex;
  flex-direction: column;
}

.user-message {
  align-items: flex-end;
}

.assistant-message {
  align-items: flex-start;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  max-inline-size: 90%;
}

.user-message .message-content-wrapper {
  align-items: flex-end;
}

.assistant-message .message-content-wrapper {
  align-items: flex-start;
}

/* Message Bubble */
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  overflow-wrap: break-word;
}

.user-bubble {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
  border-end-end-radius: 4px;
}

.assistant-bubble {
  background: var(--ds-color-static-white);
  border: 1px solid var(--ds-color-gray-100);
  border-end-start-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.processing-bubble {
  display: flex;
  align-items: center;
  padding: 14px 18px;
}

/* Message Meta */
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-block-start: 6px;
  padding: 0 4px;
}

.message-time {
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-gray-400);
}

/* Response Content */
.response-content {
  font-size: var(--ds-font-size-body);
  line-height: 1.65;
  color: var(--ds-color-gray-800);
}

/* Streaming Dots */
.streaming-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.streaming-dots .dot {
  inline-size: 6px;
  block-size: 6px;
  background: var(--ds-color-primary);
  border-radius: 50%;
  animation: ds-dot-pulse 1.4s var(--ds-ease-in-out) infinite;
}

.streaming-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

/* Workflow Section */
.workflow-section {
  margin-block-end: 14px;
  padding-block-end: 14px;
  border-block-end: 1px solid var(--ds-color-gray-100);
}

.workflow-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  padding: 6px 0;
}

.workflow-toggle:hover {
  opacity: 0.8;
}

.workflow-toggle-text {
  font-size: var(--ds-font-size-label);
  font-weight: 500;
  color: var(--ds-color-gray-600);
  flex: 1;
}

.workflow-timeline {
  margin-block-start: 16px;
  padding-inline-start: 0;
}

.workflow-step {
  display: flex;
  gap: 14px;
  position: relative;
}

.workflow-step-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  inline-size: 32px;
}

.workflow-step-icon-circle {
  inline-size: 28px;
  block-size: 28px;
  border-radius: 50%;
  background: var(--ds-color-gray-400);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
}

.workflow-step-icon-circle.workflow-step-dot--indigo {
  background: linear-gradient(135deg, #7986cb, #5c6bc0);
}

.workflow-step-icon-circle.workflow-step-dot--purple {
  background: linear-gradient(135deg, #ba68c8, #ab47bc);
}

.workflow-step-icon-circle.workflow-step-dot--orange {
  background: linear-gradient(135deg, #ffb74d, #ff9800);
}

.workflow-step-icon-circle.workflow-step-dot--cyan {
  background: linear-gradient(135deg, #4dd0e1, #26c6da);
}

.workflow-step-icon-circle.workflow-step-dot--teal {
  background: linear-gradient(135deg, #4db6ac, #26a69a);
}

.workflow-step-icon-circle.workflow-step-dot--grey {
  background: linear-gradient(135deg, #b0bec5, #90a4ae);
}

.workflow-step-line {
  inline-size: 1px;
  flex: 1;
  min-block-size: 24px;
  background: var(--ds-color-gray-200);
  margin: 6px 0;
}

.workflow-step-content {
  flex: 1;
  padding-block: 4px 20px;
  min-inline-size: 0;
}

.workflow-step--last .workflow-step-content {
  padding-block-end: 0;
}

.workflow-step-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.workflow-step-tool {
  font-size: var(--ds-font-size-body);
  font-weight: 600;
  color: var(--ds-color-gray-900);
  line-height: 1.3;
}

.workflow-step-args {
  margin-block-start: 12px;
  padding: 10px 12px;
  background: var(--ds-color-gray-50);
  border-radius: 8px;
  border: 1px solid var(--ds-color-gray-100);
}

.workflow-args-label {
  font-size: var(--ds-font-size-sm);
  font-weight: 600;
  color: var(--ds-color-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-block-end: 8px;
}

.workflow-arg {
  display: flex;
  gap: 8px;
  font-size: var(--ds-font-size-caption);
  line-height: 1.6;
  margin-block-end: 4px;
}

.workflow-arg:last-child {
  margin-block-end: 0;
}

.workflow-arg-key {
  color: #9575cd;
  font-weight: 500;
  flex-shrink: 0;
}

/* Sources Section */
.sources-section {
  margin-block-start: 10px;
  padding-block-start: 10px;
  border-block-start: 1px solid var(--ds-color-gray-100);
}

.sources-header {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
}

.sources-header:hover .sources-label {
  color: var(--ds-color-gray-700);
}

.sources-label {
  font-size: var(--ds-font-size-sm);
  font-weight: 500;
  color: var(--ds-color-gray-500);
  transition: color 0.15s ease;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-block-start: 6px;
}

.source-document-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-document-group-header {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  background: linear-gradient(135deg, var(--ds-color-gray-50) 0%, var(--ds-color-gray-100) 100%);
  border-radius: 5px;
  cursor: pointer;
  text-decoration: none;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}

.source-document-group-header:hover {
  background: linear-gradient(135deg, #e8eaff 0%, #dfe1ff 100%);
}

.source-document-group-header:hover .source-document-link-icon {
  opacity: 1;
  color: var(--ds-color-primary);
}

.source-document-group-title {
  font-size: var(--ds-font-size-sm);
  font-weight: 600;
  color: var(--ds-color-gray-700);
  flex: 1;
  min-inline-size: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-document-link-icon {
  opacity: 0.5;
  transition: var(--ds-transition-colors), var(--ds-transition-opacity);
}

.source-document-chunks {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-inline-start: 20px;
}

.source-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 4px 4px;
  background: var(--ds-color-gray-50);
  border-radius: 4px;
  cursor: pointer;
  transition: var(--ds-transition-colors);
}

.source-chip:hover {
  background: #e8eaff;
}

.source-chip:hover .source-chip-num {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}

.source-chip-num {
  display: flex;
  align-items: center;
  justify-content: center;
  min-inline-size: 14px;
  block-size: 14px;
  font-size: 9px;
  font-weight: 600;
  color: var(--ds-color-primary);
  background: var(--ds-color-gray-200);
  border-radius: 3px;
  transition: var(--ds-transition-colors);
}

.source-chip-title {
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-gray-700);
  flex: 1;
  min-inline-size: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Source Dialog */
.source-dialog-card {
  inline-size: 480px;
  max-inline-size: 100vi;
  block-size: 100%;
  display: flex;
  flex-direction: column;
}

.source-dialog-header {
  flex-shrink: 0;
  background: var(--ds-color-gray-50);
}

.source-document-link {
  color: #6c5ce7;
  text-decoration: none;
  border-block-end: 1px solid transparent;
  transition: border-color 0.2s ease;
  max-inline-size: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.source-document-link:hover {
  border-block-end-color: #6c5ce7;
}

.source-dialog-content {
  flex: 1;
  overflow-block: auto;
  padding: 20px;
}

.source-full-text {
  font-size: var(--ds-font-size-body);
  line-height: 1.7;
  color: var(--ds-color-gray-700);
  overflow-wrap: break-word;
}

/* Input Area */
.input-area {
  flex-shrink: 0;
  padding: 16px;
  background: var(--ds-color-static-white);
  border-block-start: 1px solid var(--ds-color-gray-100);
}

.input-form {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.message-input {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
}

/* Empty Response State */
.empty-response {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: linear-gradient(135deg, var(--ds-color-gray-50) 0%, var(--ds-color-gray-50) 100%);
  border-radius: 10px;
  border: 1px dashed var(--ds-color-gray-200);
}

.empty-response-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 32px;
  block-size: 32px;
  background: var(--ds-color-static-white);
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.empty-response-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
