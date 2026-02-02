<template>
  <div class="retrieval-test-drawer">
    <!-- Header -->
    <div class="drawer-header">
      <div class="header-content">
        <div class="header-title">
          <div class="km-heading-7">Test Retrieval</div>
          <div class="km-description text-secondary-text">Ask questions about your knowledge base</div>
        </div>
        <div class="header-actions">
          <km-btn v-if="messages.length > 0" flat icon="fas fa-rotate-right" icon-size="14px" size="sm" label="Clear" @click="clearChat" />
          <q-btn flat round dense icon="close" size="sm" @click="$emit('close')" />
        </div>
      </div>
    </div>

    <q-separator />

    <!-- Messages Area -->
    <div ref="messagesContainer" class="messages-area">
      <!-- Empty State -->
      <div v-if="messages.length === 0 && !processing" class="empty-state">
        <q-icon name="fas fa-comments" size="48px" color="grey-4" />
        <div class="km-heading-6 q-mt-md text-secondary-text">Start a conversation</div>
        <div class="km-description text-grey-6 q-mt-xs">Ask questions to test your retrieval configuration</div>
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
                    <q-icon name="fas fa-diagram-project" size="14px" color="teal-7" />
                    <span class="km-field text-teal-7">Execution Flow</span>
                    <q-icon :name="msg.workflowExpanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" size="12px" color="teal-7" />
                  </div>

                  <q-slide-transition>
                    <div v-show="msg.workflowExpanded" class="workflow-timeline">
                      <div
                        v-for="(step, idx) in msg.workflow"
                        :key="idx"
                        class="workflow-step"
                        :class="{ 'workflow-step--last': idx === msg.workflow.length - 1 }"
                      >
                        <div class="workflow-step-marker">
                          <div class="workflow-step-icon-circle" :class="getToolDotClass(step.tool)">
                            <q-icon :name="getToolIcon(step.tool)" size="14px" color="white" />
                          </div>
                          <div class="workflow-step-line" />
                        </div>
                        <div class="workflow-step-content">
                          <div class="workflow-step-header cursor-pointer" @click="step.expanded = !step.expanded">
                            <div class="row items-center justify-between">
                              <span class="workflow-step-tool">{{ formatToolName(step.tool) }}</span>
                              <q-icon :name="step.expanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" size="10px" color="grey-6" />
                            </div>
                            <div style="font-size: 12px; font-weight: 400">
                              <span class="text-grey-6">Step {{ step.iteration }}</span>
                              <span v-if="step.call_summary?.result_count" class="text-grey-6 q-ml-xs">•</span>
                              <span v-if="typeof step.call_summary?.result_count === 'number'" class="text-green-8">
                                Found {{ step.call_summary?.result_count }} record{{ step.call_summary?.result_count > 1 ? 's' : '' }}
                              </span>
                            </div>
                          </div>
                          <q-slide-transition>
                            <div v-show="step.expanded">
                              <div v-if="Object.keys(step.arguments || {}).length > 0" class="workflow-step-args">
                                <div class="workflow-args-label">Arguments</div>
                                <div v-for="(value, key) in step.arguments" :key="key" class="workflow-arg">
                                  <span class="workflow-arg-key">{{ key }}:</span>
                                  <span class="text-grey-9" style="font-size: 12px">{{ formatArgValue(value) }}</span>
                                </div>
                              </div>
                              <div v-if="step.call_summary.reasoning" class="workflow-step-args">
                                <div class="workflow-args-label">Reasoning</div>
                                <div class="text-grey-9" style="font-size: 12px">{{ step.call_summary?.reasoning }}</div>
                              </div>
                            </div>
                          </q-slide-transition>
                        </div>
                      </div>
                    </div>
                  </q-slide-transition>
                </div>

                <!-- Response Content -->
                <div v-if="msg.content" class="response-content">
                  <div v-if="props.outputFormat === 'plain'" class="plain-text-content">{{ msg.content }}</div>
                  <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)" />
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
                    <span class="km-description text-grey-6">No text response generated</span>
                  </div>
                </div>

                <!-- Sources Section -->
                <div v-if="msg.sources && msg.sources.length > 0" class="sources-section">
                  <div class="sources-header" @click="msg.sourcesExpanded = !msg.sourcesExpanded">
                    <q-icon name="fas fa-paperclip" size="11px" color="grey-7" />
                    <span class="sources-label">{{ msg.sources.length }} source{{ msg.sources.length > 1 ? 's' : '' }}</span>
                    <q-icon :name="msg.sourcesExpanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" size="10px" color="grey-5" />
                  </div>

                  <q-slide-transition>
                    <div v-show="msg.sourcesExpanded" class="sources-list">
                      <div v-for="group in groupSourcesByDocument(msg.sources)" :key="group.document_id" class="source-document-group">
                        <router-link
                          :to="{ name: 'KnowledgeGraphDocumentDetail', params: { id: graphId, documentId: group.document_id } }"
                          class="source-document-group-header"
                          target="_blank"
                          rel="noopener"
                          @click.stop
                        >
                          <q-icon name="description" size="12px" color="grey-7" />
                          <span class="source-document-group-title">{{ truncate(group.document_name, 35) }}</span>
                          <q-icon name="open_in_new" size="10px" color="grey-5" class="source-document-link-icon" />
                        </router-link>
                        <div class="source-document-chunks">
                          <div v-for="(source, idx) in group.sources" :key="idx" class="source-chip" @click="openSourceDetail(source)">
                            <span class="source-chip-num">{{ source.globalIndex }}</span>
                            <span class="source-chip-title">{{ truncate(source.chunk_title || 'Untitled', 40) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </q-slide-transition>
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
              <q-spinner-dots size="24px" color="primary" />
              <span class="km-description text-secondary-text q-ml-sm">Thinking...</span>
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
          placeholder="Ask a question..."
          autogrow
          border-radius="8px"
          class="message-input"
          @keydown.enter="handleEnter"
        />
        <q-btn type="submit" color="primary" unelevated round :disable="!canSend" :loading="processing" padding="8px" class="send-btn">
          <q-icon name="fas fa-paper-plane" size="14px" />
        </q-btn>
      </form>
    </div>

    <!-- Source Detail Dialog -->
    <q-dialog v-model="showSourceDialog" position="right" maximized>
      <q-card class="source-dialog-card">
        <q-card-section class="source-dialog-header">
          <div class="row items-start no-wrap">
            <div class="col">
              <div class="row items-center no-wrap">
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
            <q-btn flat round dense icon="close" @click="showSourceDialog = false" />
          </div>
        </q-card-section>
        <q-separator />
        <q-card-section class="source-dialog-content">
          <div class="source-full-text markdown-content" v-html="renderMarkdown(selectedSource?.chunk_content || '')" />
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import MarkdownIt from 'markdown-it'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { tools } from './models'

// Initialize markdown-it with sensible defaults
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
})

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

const store = useStore()

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

const renderMarkdown = (text: string): string => {
  if (!text) return ''
  return md.render(text)
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
    findChunksBySimilarity: 'fas fa-search',
    findDocumentsBySummarySimilarity: 'filter_alt',
    findDocumentsByMetadata: 'fas fa-tags',
    findDocumentsByEntitySimilarity: 'fas fa-project-diagram',
    exit: 'fas fa-sign-out-alt',
  }
  return icons[tool] || 'fas fa-cog'
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
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
        content: 'Retrieval failed. Please check server logs.',
        timestamp: new Date(),
      }
      messages.value.push(assistantMessage)
    }
  } catch (err) {
    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: 'An error occurred while contacting the retrieval service.',
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
.retrieval-test-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 420px;
  min-width: 420px;
  max-width: 420px;
  background: #f8f9fa;
  border-left: 1px solid var(--border-color, #e0e0e0);
}

/* Header */
.drawer-header {
  flex-shrink: 0;
  padding: 16px 20px;
  background: #fff;
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
  overflow-y: auto;
  padding: 16px;
}

.messages-area::-webkit-scrollbar {
  width: 6px;
}

.messages-area::-webkit-scrollbar-track {
  background: transparent;
}

.messages-area::-webkit-scrollbar-thumb {
  background: #e0e0e0;
  border-radius: 3px;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: #bdbdbd;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
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
  max-width: 90%;
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
  word-wrap: break-word;
}

.user-bubble {
  background: var(--q-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant-bubble {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-bottom-left-radius: 4px;
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
  margin-top: 6px;
  padding: 0 4px;
}

.message-time {
  font-size: 11px;
  color: #9e9e9e;
}

/* Response Content */
.response-content {
  font-size: 14px;
  line-height: 1.65;
  color: #2d3436;
}

/* Plain Text Content */
.plain-text-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family:
    'SF Pro Text',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    sans-serif;
}

/* Markdown Content Styling */
.markdown-content :deep(p) {
  margin: 0 0 14px 0;
  color: #2d3436;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1a1a1a;
}

.markdown-content :deep(em) {
  font-style: italic;
  color: #4a5568;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-weight: 600;
  color: #1a1a1a;
  margin: 18px 0 10px 0;
  line-height: 1.3;
}

.markdown-content :deep(h1) {
  font-size: 1.4em;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 1.25em;
  padding-bottom: 6px;
}

.markdown-content :deep(h3) {
  font-size: 1.1em;
}

.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-size: 1em;
}

.markdown-content :deep(h1:first-child),
.markdown-content :deep(h2:first-child),
.markdown-content :deep(h3:first-child) {
  margin-top: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 6px 0;
  padding-left: 4px;
}

.markdown-content :deep(li::marker) {
  color: #6c5ce7;
}

.markdown-content :deep(ul li) {
  list-style-type: disc;
}

.markdown-content :deep(ul ul li) {
  list-style-type: circle;
}

.markdown-content :deep(ol li) {
  list-style-type: decimal;
}

.markdown-content :deep(blockquote) {
  margin: 14px 0;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f5f6fa 100%);
  border-left: 4px solid #6c5ce7;
  border-radius: 0 8px 8px 0;
  color: #4a5568;
  font-style: italic;
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

.markdown-content :deep(code) {
  background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f4 100%);
  padding: 3px 8px;
  border-radius: 5px;
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
  font-size: 0.88em;
  color: #d63384;
  border: 1px solid #e9ecef;
}

.markdown-content :deep(pre) {
  margin: 14px 0;
  padding: 16px;
  background: linear-gradient(135deg, #2d3436 0%, #1e272e 100%);
  border-radius: 10px;
  overflow-x: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  border: none;
  color: #e8e8e8;
  font-size: 0.85em;
  line-height: 1.6;
}

.markdown-content :deep(a) {
  color: #6c5ce7;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s ease;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: #6c5ce7;
}

.markdown-content :deep(hr) {
  border: none;
  height: 2px;
  background: linear-gradient(90deg, transparent, #e8e8e8, transparent);
  margin: 20px 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
  font-size: 0.92em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 10px 14px;
  text-align: left;
  border: 1px solid #e8e8e8;
}

.markdown-content :deep(th) {
  background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f4 100%);
  font-weight: 600;
  color: #1a1a1a;
}

.markdown-content :deep(tr:nth-child(even)) {
  background: #fafafa;
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 12px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Streaming Dots */
.streaming-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.streaming-dots .dot {
  width: 6px;
  height: 6px;
  background: var(--q-primary);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.streaming-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Workflow Section */
.workflow-section {
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f0f0f0;
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
  font-size: 13px;
  font-weight: 500;
  color: #616161;
  flex: 1;
}

.workflow-timeline {
  margin-top: 16px;
  padding-left: 0;
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
  width: 32px;
}

.workflow-step-icon-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #9e9e9e;
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
  width: 1px;
  flex: 1;
  min-height: 24px;
  background: #e0e0e0;
  margin: 6px 0;
}

.workflow-step-content {
  flex: 1;
  padding-bottom: 20px;
  min-width: 0;
  padding-top: 4px;
}

.workflow-step--last .workflow-step-content {
  padding-bottom: 0;
}

.workflow-step-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.workflow-step-tool {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.3;
}

.workflow-step-args {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.workflow-args-label {
  font-size: 11px;
  font-weight: 600;
  color: #757575;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.workflow-arg {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.6;
  margin-bottom: 4px;
}

.workflow-arg:last-child {
  margin-bottom: 0;
}

.workflow-arg-key {
  color: #9575cd;
  font-weight: 500;
  flex-shrink: 0;
}

/* Sources Section */
.sources-section {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
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
  color: #424242;
}

.sources-label {
  font-size: 11px;
  font-weight: 500;
  color: #757575;
  transition: color 0.15s ease;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 6px;
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
  background: linear-gradient(135deg, #f8f9fa 0%, #f0f1f3 100%);
  border-radius: 5px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}

.source-document-group-header:hover {
  background: linear-gradient(135deg, #e8eaff 0%, #dfe1ff 100%);
}

.source-document-group-header:hover .source-document-link-icon {
  opacity: 1;
  color: var(--q-primary);
}

.source-document-group-title {
  font-size: 11px;
  font-weight: 600;
  color: #424242;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-document-link-icon {
  opacity: 0.5;
  transition: all 0.15s ease;
}

.source-document-chunks {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 20px;
}

.source-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 4px 4px;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.12s ease;
}

.source-chip:hover {
  background: #e8eaff;
}

.source-chip:hover .source-chip-num {
  background: var(--q-primary);
  color: #fff;
}

.source-chip-num {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 14px;
  height: 14px;
  font-size: 9px;
  font-weight: 600;
  color: var(--q-primary);
  background: #e0e0e0;
  border-radius: 3px;
  transition: all 0.12s ease;
}

.source-chip-title {
  font-size: 11px;
  color: #424242;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Source Dialog */
.source-dialog-card {
  width: 480px;
  max-width: 100vw;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.source-dialog-header {
  flex-shrink: 0;
  background: #fafafa;
}

.source-document-link {
  color: #6c5ce7;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s ease;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.source-document-link:hover {
  border-bottom-color: #6c5ce7;
}

.source-dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.source-full-text {
  font-size: 14px;
  line-height: 1.7;
  color: #424242;
  word-wrap: break-word;
}

/* Input Area */
.input-area {
  flex-shrink: 0;
  padding: 16px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
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
  background: linear-gradient(135deg, #f8f9fa 0%, #f5f6f7 100%);
  border-radius: 10px;
  border: 1px dashed #e0e0e0;
}

.empty-response-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.empty-response-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
