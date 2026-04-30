<script setup lang="ts">
import { computed, ref } from 'vue'
// @ts-ignore Vite/Nx resolves the workspace alias; VS Code may attach new app files to the local tsconfig before Nx paths are applied.
import * as primitives from '@ds/primitives'
// @ts-ignore Vite/Nx resolves the workspace alias; VS Code may attach new app files to the local tsconfig before Nx paths are applied.
import { AgentMessage, RetrievalAnswer, SearchAnswer, SearchPrompt } from '@ui'

const {
  DsBadge,
  DsButton,
  DsButtonGroup,
  DsButtonGroupSeparator,
  DsButtonGroupText,
  DsContextMenu,
  DsContextMenuContent,
  DsContextMenuItem,
  DsContextMenuSeparator,
  DsContextMenuTrigger,
  DsDropdownMenu,
  DsDropdownMenuContent,
  DsDropdownMenuItem,
  DsDropdownMenuLabel,
  DsDropdownMenuRoot,
  DsDropdownMenuSeparator,
  DsDropdownMenuSub,
  DsDropdownMenuSubContent,
  DsDropdownMenuSubTrigger,
  DsDropdownMenuTrigger,
  DsField,
  DsFieldDescription,
  DsFieldError,
  DsFieldLabel,
  DsInput,
  DsInputGroup,
  DsInputGroupAddon,
  DsInputGroupButton,
  DsInputGroupInput,
  DsInputGroupText,
  DsNativeSelect,
  DsSelect,
  DsTabs,
  DsTextarea,
} = primitives

interface GalleryOption {
  label: string
  value: string
  meta?: string
  disabled?: boolean
}

interface InventoryStat {
  family: string
  count: number
  note: string
  modes: string[]
}

interface ButtonSample {
  label: string
  props: Record<string, unknown>
}

type IconTone = 'default' | 'subtle' | 'muted' | 'weak' | 'brand' | 'info' | 'success' | 'warning' | 'danger' | 'inverse' | 'current'

interface GlyphSample {
  label: string
  mode: string
  name: string
  tone: IconTone
  size: string
}

interface SvgIconSample {
  label: string
  name: string
  width: string
  height: string
}

interface AgentMessageData {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content?: string
  created_at: string
  tool_call_id?: string
  tool_calls?: string
  feedback?: { type?: string }
}

const lastAction = ref('No action selected')
const toggleValue = ref('grid')
const densityToggle = ref('compact')

const textInput = ref('Knowledge graph')
const denseInput = ref('kg_documents')
const roundedInput = ref('Find document source')
const numberInput = ref(12)
const passwordInput = ref('secret-token')
const textareaInput = ref('A multi-line prompt preview keeps the same field chrome.')
const flatInput = ref('inline-title')
const dsInput = ref('Primitive input')
const dsTextarea = ref('Primitive textarea value')
const searchQuery = ref('metadata filter')

const simpleSelect = ref('active')
const dsSelect = ref('draft')
const nativeSelect = ref('active')
const multiSelect = ref(['rag', 'api'])
const customSelect = ref<GalleryOption | null>(null)
const flatSelect = ref<GalleryOption | null>(null)
const disabledSelect = ref('disabled')

const kmUnderlineTab = ref('overview')
const kmPillTab = ref('details')
const dsSegmentedTab = ref('compact')
const dsVerticalTab = ref('usage')

const selectOptions: GalleryOption[] = [
  { label: 'Draft', value: 'draft', meta: 'Hidden from users' },
  { label: 'Active', value: 'active', meta: 'Live in catalog' },
  { label: 'Archived', value: 'archived', meta: 'Read only' },
  { label: 'Disabled', value: 'disabled', meta: 'Unavailable', disabled: true },
]

const capabilityOptions: GalleryOption[] = [
  { label: 'RAG', value: 'rag', meta: 'Retrieval' },
  { label: 'API tools', value: 'api', meta: 'Actions' },
  { label: 'Knowledge graph', value: 'graph', meta: 'Entities' },
  { label: 'Note taker', value: 'notes', meta: 'Meetings' },
]

customSelect.value = capabilityOptions[0] ?? null
flatSelect.value = selectOptions[1] ?? null

const inventoryStats: InventoryStat[] = [
  {
    family: 'Chat',
    count: 7,
    note: 'ui-comp chat surfaces plus admin trace chat renderer',
    modes: ['prompt input', 'search answer', 'retrieval answer', 'agent message', 'loading answer', 'tool result'],
  },
  {
    family: 'Icon/Glyph',
    count: 647,
    note: 'icon props in templates; Phosphor is primary, legacy font/sprite paths remain transitional',
    modes: ['Phosphor canonical', 'Phosphor namespace', 'Material fallback', 'FontAwesome fallback', 'SVG brand sprite', 'icon button'],
  },
  {
    family: 'Button',
    count: 720,
    note: 'KmBtn, icon buttons, nav buttons, toggles, dropdown triggers, DsButton',
    modes: ['flat icon', 'primary submit', 'danger', 'outline', 'selected', 'dropdown', 'toggle', 'nav'],
  },
  {
    family: 'Input',
    count: 539,
    note: 'KmInput, flat input, list/chips inputs, primitive fields',
    modes: ['text', 'textarea', 'autogrow', 'readonly', 'error', 'clearable search', 'dense', 'number/password'],
  },
  {
    family: 'Select',
    count: 178,
    note: 'KmSelect simple/advanced, flat filter select, DsSelect, native select',
    modes: ['simple', 'multi chips', 'searchable', 'select all', 'custom option', 'flat filter', 'disabled/loading'],
  },
  {
    family: 'Menu',
    count: 164,
    note: 'Dropdown menu object API, primitive API, legacy KmMenu and button dropdown paths',
    modes: ['object menu', 'primitive menu', 'sub menu', 'destructive item', 'context menu', 'legacy dropdown'],
  },
  {
    family: 'Tab',
    count: 137,
    note: 'Legacy child registration plus items API on KmTabs and DsTabs',
    modes: ['underline', 'pill', 'segmented', 'vertical', 'legacy slot', 'disabled item'],
  },
]

const glyphSamples: GlyphSample[] = [
  { label: 'Phosphor primary', mode: 'name="search"', name: 'search', tone: 'default', size: '24px' },
  { label: 'Phosphor namespace', mode: 'name="ph:thumbs-up"', name: 'ph:thumbs-up', tone: 'brand', size: '24px' },
  { label: 'Canonical action', mode: 'name="copy"', name: 'copy', tone: 'subtle', size: '24px' },
  { label: 'Material fallback', mode: 'name="unknown_ligature"', name: 'unknown_ligature', tone: 'muted', size: '24px' },
  { label: 'FontAwesome fallback', mode: 'name="warning"', name: 'warning', tone: 'warning', size: '24px' },
  { label: 'Current color', mode: 'tone="current"', name: 'check', tone: 'current', size: '24px' },
]

const iconToneSamples: IconTone[] = ['default', 'subtle', 'muted', 'weak', 'brand', 'info', 'success', 'warning', 'danger', 'inverse', 'current']

const iconSizeSamples = ['12px', '16px', '20px', '24px', '32px']

const svgIconSamples: SvgIconSample[] = [
  { label: 'Magnet brand', name: 'magnet', width: '24', height: '26' },
  { label: 'Message mark', name: 'magnet-msg', width: '26', height: '26' },
  { label: 'Folder art', name: 'folder', width: '32', height: '32' },
  { label: 'Positive emoji', name: 'like-emoji', width: '28', height: '28' },
  { label: 'Empty state art', name: 'empty-collection', width: '44', height: '44' },
]

const kmButtonSamples: ButtonSample[] = [
  { label: 'Primary', props: { label: 'Primary', variant: 'primary' } },
  { label: 'Secondary', props: { label: 'Secondary', variant: 'secondary' } },
  { label: 'Tertiary', props: { label: 'Tertiary', variant: 'tertiary' } },
  { label: 'Outline', props: { label: 'Outline', variant: 'outline' } },
  { label: 'Danger', props: { label: 'Danger', variant: 'danger' } },
  { label: 'Link', props: { label: 'Link', variant: 'link' } },
  { label: 'Flat icon sm', props: { flat: true, icon: 'edit', iconSize: '16px', size: 'sm', tooltip: 'Edit' } },
  { label: 'Flat icon xs', props: { flat: true, icon: 'copy', iconSize: '16px', size: 'xs', tooltip: 'Copy' } },
  { label: 'Muted tone', props: { label: 'Muted', flat: true, tone: 'muted', icon: 'info', iconSize: '16px' } },
  { label: 'Selected', props: { label: 'Selected', flat: true, selected: true, icon: 'pin', iconSize: '16px' } },
  { label: 'Loading', props: { label: 'Loading', loading: true } },
  { label: 'Disabled', props: { label: 'Disabled', disable: true } },
]

const dsButtonSamples: ButtonSample[] = [
  { label: 'Primary', props: {} },
  { label: 'Secondary', props: { variant: 'secondary' } },
  { label: 'Outline', props: { variant: 'outline' } },
  { label: 'Ghost', props: { variant: 'ghost' } },
  { label: 'Destructive', props: { variant: 'destructive' } },
  { label: 'Link', props: { variant: 'link' } },
  { label: 'Small', props: { size: 'sm' } },
  { label: 'Large', props: { size: 'lg' } },
  { label: 'Icon', props: { size: 'icon', 'aria-label': 'Icon button' } },
]

const buttonToggleOptions = [
  { label: 'Grid', value: 'grid', icon: 'grid_view' },
  { label: 'List', value: 'list', icon: 'view_list' },
  { label: 'Raw', value: 'raw', icon: 'code' },
]

const densityOptions = [
  { label: 'Compact', value: 'compact' },
  { label: 'Roomy', value: 'roomy' },
]

const dropdownButtonOptions = [
  { label: 'Duplicate', icon: 'copy' },
  { label: 'Archive', icon: 'archive' },
  { label: 'Delete', icon: 'delete' },
]

function markAction(label: string) {
  lastAction.value = label
}

const objectMenuItems = computed(() => [
  { label: 'Open', tone: 'primary' as const, onSelect: () => markAction('Object menu: Open') },
  { label: 'Duplicate', onSelect: () => markAction('Object menu: Duplicate') },
  { label: 'Disabled action', disabled: true },
  { separator: true },
  { label: 'Delete', tone: 'danger' as const, onSelect: () => markAction('Object menu: Delete') },
])

const tabItems = [
  { label: 'Overview', value: 'overview' },
  { label: 'Details', value: 'details' },
  { label: 'Disabled', value: 'disabled', disabled: true },
]

const dsTabItems = [
  { label: 'Usage', value: 'usage' },
  { label: 'Events', value: 'events' },
  { label: 'Settings', value: 'settings' },
]

const searchAnswer = {
  id: 'search-answer-gallery',
  prompt: 'Which documents mention OAuth refresh validation?',
  answer: 'The current answer card shows a question row, generated response, feedback controls, source cards, and score chips.',
  results: [
    {
      score: 0.91,
      content: 'The auth review describes refresh token validation and rotation details.',
      metadata: { type: 'pdf', title: 'Auth Review', source: 'auth-review.pdf', pageNumber: 4 },
    },
  ],
}

const retrievalAnswer = {
  id: 'retrieval-answer-gallery',
  prompt: 'Show matching knowledge graph sources',
  answer: 'Retrieval answers use a compact source list and a resulting-prompt modal trigger.',
  loading: false,
  results: [
    {
      score: 0.86,
      content: 'Entity extraction settings and retrieval tools are configured in Knowledge Graph.',
      metadata: { type: 'pdf', title: 'Knowledge Graph Guide', source: 'kg-guide.pdf', page: 7 },
    },
  ],
}

const loadingRetrievalAnswer = {
  id: 'retrieval-answer-loading-gallery',
  prompt: 'Loading answer state',
  answer: '',
  loading: true,
  results: [],
}

const agentMessages: AgentMessageData[] = [
  {
    id: 'agent-user-gallery',
    role: 'user',
    content: 'Summarize failed retrieval runs from today.',
    created_at: '2026-04-28T08:00:00Z',
  },
  {
    id: 'agent-assistant-gallery',
    role: 'assistant',
    content: 'I found three failed runs. The most common cause is an invalid metadata filter.',
    created_at: '2026-04-28T08:00:12Z',
    feedback: { type: 'like' },
  },
  {
    id: 'agent-tool-gallery',
    role: 'tool',
    tool_call_id: 'search_logs',
    content: 'status=error count=3 source=retrieval',
    created_at: '2026-04-28T08:00:18Z',
  },
  {
    id: 'agent-tool-call-gallery',
    role: 'assistant',
    tool_calls: '{ "name": "search_logs", "arguments": { "severity": "error" } }',
    created_at: '2026-04-28T08:00:22Z',
  },
]
</script>

<template>
  <div class="dev-ui-gallery">
    <header class="dev-ui-gallery__header">
      <div>
        <p class="dev-ui-gallery__eyebrow">Dev UI Gallery</p>
        <h1>Current component modes</h1>
      </div>
      <div class="dev-ui-gallery__header-actions">
        <DsBadge display="status" tone="brand">DEV</DsBadge>
        <KmBtn label="Route" variant="outline" icon="link" size="sm" />
      </div>
    </header>

    <section class="dev-ui-gallery__section" aria-labelledby="inventory-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="inventory-title">Repository inventory</h2>
        <span>Counts and modes from current Vue templates</span>
      </div>

      <div class="dev-ui-gallery__inventory-grid">
        <article v-for="item in inventoryStats" :key="item.family" class="dev-ui-gallery__inventory-item">
          <div class="dev-ui-gallery__inventory-header">
            <h3>{{ item.family }}</h3>
            <strong>{{ item.count }}</strong>
          </div>
          <p>{{ item.note }}</p>
          <div class="dev-ui-gallery__chip-row">
            <DsBadge v-for="mode in item.modes" :key="mode" display="tag" tone="neutral">{{ mode }}</DsBadge>
          </div>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="icons-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="icons-title">Glyphs and icons</h2>
        <span>KmGlyph, KmIcon SVG sprite, icon props, icon buttons, and component-owned icon slots</span>
      </div>

      <div class="dev-ui-gallery__grid dev-ui-gallery__grid--icons">
        <article class="dev-ui-gallery__sample dev-ui-gallery__sample--wide">
          <h3>KmGlyph rendering modes</h3>
          <div class="dev-ui-gallery__icon-grid">
            <div v-for="sample in glyphSamples" :key="sample.label" class="dev-ui-gallery__icon-card">
              <span class="dev-ui-gallery__icon-preview" :class="{ 'dev-ui-gallery__icon-preview--current': sample.tone === 'current' }">
                <KmGlyph :name="sample.name" :tone="sample.tone" :size="sample.size" />
              </span>
              <strong>{{ sample.label }}</strong>
              <small>{{ sample.mode }}</small>
            </div>
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Tones and sizes</h3>
          <div class="dev-ui-gallery__icon-tone-grid">
            <span
              v-for="tone in iconToneSamples"
              :key="tone"
              class="dev-ui-gallery__tone-chip"
              :class="{ 'dev-ui-gallery__tone-chip--inverse': tone === 'inverse' }"
            >
              <KmGlyph name="check" :tone="tone" size="18px" />
              {{ tone }}
            </span>
          </div>
          <div class="dev-ui-gallery__row">
            <span v-for="size in iconSizeSamples" :key="size" class="dev-ui-gallery__icon-size-sample">
              <KmGlyph name="search" tone="brand" :size="size" />
              <small>{{ size }}</small>
            </span>
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>KmIcon SVG sprite</h3>
          <div class="dev-ui-gallery__icon-grid dev-ui-gallery__icon-grid--compact">
            <div v-for="sample in svgIconSamples" :key="sample.name" class="dev-ui-gallery__icon-card">
              <span class="dev-ui-gallery__icon-preview dev-ui-gallery__icon-preview--svg">
                <KmIcon :name="sample.name" :width="sample.width" :height="sample.height" />
              </span>
              <strong>{{ sample.label }}</strong>
              <small>name="{{ sample.name }}"</small>
            </div>
          </div>
        </article>

        <article class="dev-ui-gallery__sample dev-ui-gallery__sample--wide">
          <h3>Icon props through components</h3>
          <div class="dev-ui-gallery__row">
            <KmBtn label="Before" icon="plus" icon-size="16px" />
            <KmBtn label="After" icon-after="chevron_right" variant="secondary" icon-size="18px" />
            <KmBtn label="Standard copy" icon="copy" variant="outline" icon-size="16px" />
            <KmIconBtn icon="thumbs-up" icon-size="16px" tone="brand" aria-label="Like" />
            <KmIconBtn icon="download" icon-size="16px" aria-label="Download" />
          </div>
          <div class="dev-ui-gallery__row">
            <KmInput model-value="Search input icon" icon-before="search" readonly />
            <KmInput model-value="Phosphor prefix" icon-before="link" readonly />
          </div>
          <div class="dev-ui-gallery__row dev-ui-gallery__row--icons">
            <KmAvatar icon="format_quote" tone="brand-soft" size="40px" font-size="20px" />
            <KmAvatar icon="warning" tone="danger-soft" size="40px" font-size="20px" square />
            <KmChip icon="database" label="Source chip" display="tag" tone="neutral" dense />
            <KmChip icon="check" label="Selected" display="filter" tone="brand" dense />
            <KmBadge dot tone="danger" />
            <KmNavBtn label="Glyph nav" icon="stack" path="dev/ui-gallery" parent-route="/dev/ui-gallery" />
            <KmNavBtn label="SVG nav" svg-icon="magnet" path="dev/ui-gallery" parent-route="/dev/ui-gallery" />
          </div>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="chat-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="chat-title">Chat</h2>
        <span>Prompt, answer cards, agent bubbles, loading and tool states</span>
      </div>

      <div class="dev-ui-gallery__grid dev-ui-gallery__grid--chat">
        <article class="dev-ui-gallery__sample dev-ui-gallery__sample--wide">
          <h3>Search prompt and answer</h3>
          <div class="dev-ui-gallery__surface dev-ui-gallery__surface--chat">
            <SearchPrompt
              :t="{ placeholder: 'Ask the knowledge base' }"
              @on-load="markAction('Search prompt submitted')"
              @search="markAction('Search prompt search')"
              @search-rag="markAction('Search prompt RAG')"
              @search-rag-execute="markAction('Search prompt RAG execute')"
            />
            <SearchAnswer :answer="searchAnswer" :ui-settings="{ user_fideback: true }" @refine="markAction('Search answer refine')" />
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Retrieval answer states</h3>
          <div class="dev-ui-gallery__surface dev-ui-gallery__surface--chat">
            <RetrievalAnswer
              :answer="retrievalAnswer"
              :ui-settings="{ user_fideback: true }"
              @refine="markAction('Retrieval answer refine')"
              @feedback="markAction('Retrieval feedback')"
              @select-answer="markAction('Retrieval source selected')"
            />
            <RetrievalAnswer :answer="loadingRetrievalAnswer" />
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Agent messages</h3>
          <div class="dev-ui-gallery__surface dev-ui-gallery__surface--agent">
            <AgentMessage
              v-for="message in agentMessages"
              :key="message.id"
              :message="message"
              :last-message="message.id === 'agent-assistant-gallery'"
              :preview-mode="message.id === 'agent-tool-call-gallery'"
              @copy="markAction('Agent copy')"
              @like="markAction('Agent like')"
              @dislike="markAction('Agent dislike')"
              @delete="markAction('Agent delete')"
              @focus="markAction('Agent focus')"
              @select="markAction('Agent select')"
            />
          </div>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="buttons-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="buttons-title">Buttons</h2>
        <span>KmBtn variants, icon buttons, toggles, nav buttons, dropdown triggers, DsButton</span>
      </div>

      <div class="dev-ui-gallery__grid">
        <article class="dev-ui-gallery__sample dev-ui-gallery__sample--wide">
          <h3>KmBtn observed modes</h3>
          <div class="dev-ui-gallery__row">
            <KmBtn
              v-for="sample in kmButtonSamples"
              :key="sample.label"
              v-bind="sample.props"
              @click="markAction(`KmBtn: ${sample.label}`)"
            />
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Icon, toggle and nav</h3>
          <div class="dev-ui-gallery__row">
            <KmIconBtn icon="thumbs-up" icon-size="16px" tone="brand" aria-label="Like" />
            <KmIconBtn icon="thumbs-down" icon-size="16px" aria-label="Dislike" />
            <KmBtnToggle v-model="toggleValue" :options="buttonToggleOptions" />
            <KmBtnToggle v-model="densityToggle" :options="densityOptions" spread />
          </div>
          <div class="dev-ui-gallery__nav-row">
            <KmNavBtn label="Active nav" icon="stack" path="dev/ui-gallery" parent-route="/dev/ui-gallery" />
            <KmNavBtn label="Expanded child" icon="chevron_right" size="sm" expandable expanded />
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Dropdown and grouped buttons</h3>
          <div class="dev-ui-gallery__row">
            <KmBtn dropdown label="KmBtn dropdown" variant="outline" :options="dropdownButtonOptions" @click-option="markAction('KmBtn dropdown item')" />
            <DsDropdownMenu :items="objectMenuItems" align="end">
              <template #trigger>
                <KmBtn label="Object menu" variant="secondary" icon-after="chevron-down" />
              </template>
            </DsDropdownMenu>
          </div>
          <DsButtonGroup>
            <DsButtonGroupText>View</DsButtonGroupText>
            <DsButton variant="ghost" size="sm">Grid</DsButton>
            <DsButtonGroupSeparator />
            <DsButton variant="ghost" size="sm">List</DsButton>
          </DsButtonGroup>
        </article>

        <article class="dev-ui-gallery__sample dev-ui-gallery__sample--wide">
          <h3>DsButton primitive</h3>
          <div class="dev-ui-gallery__row">
            <DsButton v-for="sample in dsButtonSamples" :key="sample.label" v-bind="sample.props">
              {{ sample.label === 'Icon' ? 'S' : sample.label }}
            </DsButton>
            <DsButton block justify="between" variant="outline">Block between <span>Cmd K</span></DsButton>
          </div>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="inputs-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="inputs-title">Inputs</h2>
        <span>Text, textarea, autogrow, readonly, error, clearable search, dense, primitive field</span>
      </div>

      <div class="dev-ui-gallery__grid dev-ui-gallery__grid--forms">
        <article class="dev-ui-gallery__sample">
          <h3>KmInput common modes</h3>
          <KmInput v-model="textInput" label="Label with clear" clearable icon-before="graph" suffix="id" />
          <KmInput v-model="denseInput" label="Dense prefix" dense prefix="#" />
          <KmInput v-model="roundedInput" placeholder="Rounded search" rounded clearable icon-before="search" />
          <KmInput v-model="numberInput" label="Number" type="number" />
          <KmInput v-model="passwordInput" label="Password" type="password" autocomplete="current-password" />
          <KmInput model-value="Read only value" label="Readonly" readonly />
          <KmInput model-value="Broken value" label="Error" error-message="Validation message" />
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Textareas and inline inputs</h3>
          <KmInput v-model="textareaInput" label="Textarea" type="textarea" autogrow :rows="3" />
          <KmInputFlat v-model="flatInput" />
          <DsField>
            <DsFieldLabel for="gallery-ds-input">DsField label</DsFieldLabel>
            <DsInput id="gallery-ds-input" v-model="dsInput" placeholder="Primitive input" />
            <DsFieldDescription>Helper text uses DsFieldDescription.</DsFieldDescription>
          </DsField>
          <DsField data-invalid="true">
            <DsFieldLabel for="gallery-ds-input-error">Primitive error</DsFieldLabel>
            <DsInput id="gallery-ds-input-error" aria-invalid="true" model-value="Invalid" />
            <DsFieldError>Primitive error message.</DsFieldError>
          </DsField>
          <DsTextarea v-model="dsTextarea" rows="3" />
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Input group pattern</h3>
          <DsInputGroup>
            <DsInputGroupAddon>
              <DsInputGroupText>https://</DsInputGroupText>
            </DsInputGroupAddon>
            <DsInputGroupInput v-model="searchQuery" aria-label="Input group" />
            <DsInputGroupAddon align="inline-end">
              <DsInputGroupButton>Go</DsInputGroupButton>
            </DsInputGroupAddon>
          </DsInputGroup>
          <DsInputGroup>
            <DsInputGroupAddon>
              <DsInputGroupText>Filter</DsInputGroupText>
            </DsInputGroupAddon>
            <DsInputGroupInput model-value="status:error" aria-label="Filter query" />
          </DsInputGroup>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="selects-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="selects-title">Selects</h2>
        <span>Simple, multi chips, searchable, select-all, custom option, flat filter, native</span>
      </div>

      <div class="dev-ui-gallery__grid dev-ui-gallery__grid--forms">
        <article class="dev-ui-gallery__sample">
          <h3>KmSelect paths</h3>
          <KmSelect v-model="simpleSelect" :options="selectOptions" emit-value map-options placeholder="Simple KmSelect" />
          <KmSelect
            v-model="multiSelect"
            :options="capabilityOptions"
            multiple
            use-chips
            emit-value
            map-options
            has-dropdown-search
            select-all
            placeholder="Advanced multi-select"
          />
          <KmSelect v-model="customSelect" :options="capabilityOptions" placeholder="Custom option slot">
            <template #option="{ opt }">
              <span class="dev-ui-gallery__option">
                <strong>{{ opt.label }}</strong>
                <small>{{ opt.meta }}</small>
              </span>
            </template>
          </KmSelect>
          <KmSelect v-model="disabledSelect" :options="selectOptions" disabled placeholder="Disabled select" />
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Flat, primitive and native</h3>
          <KmSelectFlat v-model="flatSelect" :options="selectOptions" show-label />
          <DsSelect v-model="dsSelect" :options="selectOptions" placeholder="DsSelect" />
          <DsNativeSelect v-model="nativeSelect" aria-label="Native select">
            <option v-for="option in selectOptions" :key="option.value" :value="option.value" :disabled="option.disabled">
              {{ option.label }}
            </option>
          </DsNativeSelect>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="menus-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="menus-title">Menus</h2>
        <span>Object API, primitive menu, sub menu, context menu, legacy dropdown shims</span>
      </div>

      <div class="dev-ui-gallery__grid">
        <article class="dev-ui-gallery__sample">
          <h3>Live triggers</h3>
          <div class="dev-ui-gallery__row">
            <DsDropdownMenu :items="objectMenuItems" align="start">
              <template #trigger>
                <DsButton variant="outline">Object API</DsButton>
              </template>
            </DsDropdownMenu>

            <DsDropdownMenuRoot>
              <DsDropdownMenuTrigger as-child>
                <DsButton variant="secondary">Primitive API</DsButton>
              </DsDropdownMenuTrigger>
              <DsDropdownMenuContent align="start">
                <DsDropdownMenuLabel>Actions</DsDropdownMenuLabel>
                <DsDropdownMenuItem @select="markAction('Primitive menu: Edit')">Edit</DsDropdownMenuItem>
                <DsDropdownMenuItem @select="markAction('Primitive menu: Duplicate')">Duplicate</DsDropdownMenuItem>
                <DsDropdownMenuSub>
                  <DsDropdownMenuSubTrigger>Move to</DsDropdownMenuSubTrigger>
                  <DsDropdownMenuSubContent>
                    <DsDropdownMenuItem>Archive</DsDropdownMenuItem>
                    <DsDropdownMenuItem>Backlog</DsDropdownMenuItem>
                  </DsDropdownMenuSubContent>
                </DsDropdownMenuSub>
                <DsDropdownMenuSeparator />
                <DsDropdownMenuItem variant="destructive" @select="markAction('Primitive menu: Delete')">Delete</DsDropdownMenuItem>
              </DsDropdownMenuContent>
            </DsDropdownMenuRoot>

            <span class="dev-ui-gallery__menu-anchor">
              <KmBtn label="KmMenu" flat icon-after="chevron-down" />
              <KmMenu anchor="bottom left">
                <button type="button" class="ds-menu__item">Legacy slot action</button>
              </KmMenu>
            </span>
          </div>
          <p class="dev-ui-gallery__event">{{ lastAction }}</p>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Always-visible menu preview</h3>
          <div class="ds-menu dev-ui-gallery__menu-preview">
            <div class="ds-menu__item" data-tone="primary">Primary action</div>
            <div class="ds-menu__item">Neutral action</div>
            <div class="ds-menu__item" data-disabled>Disabled action</div>
            <div class="ds-menu__separator" />
            <div class="ds-menu__item" data-tone="danger">Destructive action</div>
          </div>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Context menu</h3>
          <DsContextMenu>
            <DsContextMenuTrigger as-child>
              <div class="dev-ui-gallery__context-target" tabindex="0">Context target</div>
            </DsContextMenuTrigger>
            <DsContextMenuContent>
              <DsContextMenuItem @select="markAction('Context menu: Open')">Open</DsContextMenuItem>
              <DsContextMenuItem @select="markAction('Context menu: Rename')">Rename</DsContextMenuItem>
              <DsContextMenuSeparator />
              <DsContextMenuItem variant="destructive" @select="markAction('Context menu: Delete')">Delete</DsContextMenuItem>
            </DsContextMenuContent>
          </DsContextMenu>
          <p class="dev-ui-gallery__event">Right click or keyboard-open the target.</p>
        </article>
      </div>
    </section>

    <section class="dev-ui-gallery__section" aria-labelledby="tabs-title">
      <div class="dev-ui-gallery__section-heading">
        <h2 id="tabs-title">Tabs</h2>
        <span>Underline, pill, segmented, vertical, legacy slot registration, disabled items</span>
      </div>

      <div class="dev-ui-gallery__grid">
        <article class="dev-ui-gallery__sample dev-ui-gallery__sample--wide">
          <h3>KmTabs items API</h3>
          <KmTabs v-model="kmUnderlineTab" :items="tabItems" variant="underline">
            <template #panel-overview>Overview panel content</template>
            <template #panel-details>Details panel content</template>
          </KmTabs>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>Legacy slot registration</h3>
          <KmTabs v-model="kmPillTab" variant="pill" dense no-caps>
            <KmTab name="details" label="Details" />
            <KmTab name="activity" label="Activity" />
            <template #panel-details>Details slot panel</template>
            <template #panel-activity>Activity slot panel</template>
          </KmTabs>
        </article>

        <article class="dev-ui-gallery__sample">
          <h3>DsTabs variants</h3>
          <DsTabs v-model="dsSegmentedTab" :items="[{ label: 'Compact', value: 'compact' }, { label: 'Roomy', value: 'roomy' }]" variant="segmented">
            <template #panel-compact>Segmented compact panel</template>
            <template #panel-roomy>Segmented roomy panel</template>
          </DsTabs>
          <DsTabs v-model="dsVerticalTab" :items="dsTabItems" orientation="vertical" variant="underline">
            <template #panel-usage>Usage content</template>
            <template #panel-events>Events content</template>
            <template #panel-settings>Settings content</template>
          </DsTabs>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dev-ui-gallery {
  box-sizing: border-box;
  block-size: 100%;
  min-block-size: 0;
  inline-size: 100%;
  overflow: auto;
  padding: var(--ds-space-2xl);
  background: var(--ds-color-panel-main-bg);
  color: var(--ds-color-black);
}

.dev-ui-gallery__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ds-space-lg);
  margin-block-end: var(--ds-space-2xl);
}

.dev-ui-gallery__header-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  flex-wrap: wrap;
  justify-content: flex-end;
}

.dev-ui-gallery__eyebrow {
  margin: 0 0 var(--ds-space-2xs);
  color: var(--ds-color-primary);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}

.dev-ui-gallery h1,
.dev-ui-gallery h2,
.dev-ui-gallery h3,
.dev-ui-gallery p {
  margin: 0;
}

.dev-ui-gallery h1 {
  font-size: var(--ds-font-size-h2);
  line-height: var(--ds-line-height-tight);
}

.dev-ui-gallery h2 {
  font-size: var(--ds-font-size-h4);
  line-height: var(--ds-line-height-tight);
}

.dev-ui-gallery h3 {
  color: var(--ds-color-secondary-text);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}

.dev-ui-gallery__section {
  padding-block: var(--ds-space-xl);
  border-block-start: 1px solid var(--ds-color-border);
}

.dev-ui-gallery__section:first-of-type {
  padding-block-start: 0;
  border-block-start: 0;
}

.dev-ui-gallery__section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--ds-space-md);
  margin-block-end: var(--ds-space-md);
}

.dev-ui-gallery__section-heading span {
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
}

.dev-ui-gallery__inventory-grid,
.dev-ui-gallery__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 360px), 1fr));
  gap: var(--ds-space-md);
  align-items: start;
}

.dev-ui-gallery__inventory-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
}

.dev-ui-gallery__grid--forms {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr));
}

.dev-ui-gallery__grid--chat {
  grid-template-columns: minmax(0, 1.15fr) minmax(min(100%, 420px), 0.85fr);
}

.dev-ui-gallery__grid--icons {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr));
}

.dev-ui-gallery__inventory-item,
.dev-ui-gallery__sample {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  min-inline-size: 0;
  padding: var(--ds-space-lg);
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: 8px;
}

.dev-ui-gallery__inventory-item {
  block-size: 100%;
}

.dev-ui-gallery__inventory-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-md);
}

.dev-ui-gallery__inventory-header strong {
  color: var(--ds-color-primary);
  font-size: var(--ds-font-size-h4);
  line-height: var(--ds-line-height-tight);
}

.dev-ui-gallery__inventory-item p,
.dev-ui-gallery__event {
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
  line-height: var(--ds-line-height-relaxed);
}

.dev-ui-gallery__sample--wide {
  grid-column: span 2;
}

.dev-ui-gallery__row,
.dev-ui-gallery__chip-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ds-space-sm);
  min-inline-size: 0;
}

.dev-ui-gallery__chip-row {
  gap: var(--ds-space-xs);
}

.dev-ui-gallery__icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));
  gap: var(--ds-space-sm);
}

.dev-ui-gallery__icon-grid--compact {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 120px), 1fr));
}

.dev-ui-gallery__icon-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--ds-space-2xs);
  min-inline-size: 0;
  padding: var(--ds-space-md);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: 8px;
}

.dev-ui-gallery__icon-card strong {
  color: var(--ds-color-black);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}

.dev-ui-gallery__icon-card small,
.dev-ui-gallery__icon-size-sample small {
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-xs);
}

.dev-ui-gallery__icon-preview {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 40px;
  block-size: 40px;
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
}

.dev-ui-gallery__icon-preview--current {
  color: var(--ds-color-primary);
}

.dev-ui-gallery__icon-preview--svg {
  color: var(--ds-color-black);
}

.dev-ui-gallery__icon-tone-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ds-space-xs);
}

.dev-ui-gallery__tone-chip,
.dev-ui-gallery__icon-size-sample {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-xs);
  min-block-size: 30px;
  padding-inline: var(--ds-space-sm);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  color: var(--ds-color-secondary-text);
  font-size: var(--ds-font-size-xs);
}

.dev-ui-gallery__tone-chip--inverse {
  background: var(--ds-color-black);
  color: var(--ds-color-static-white);
}

.dev-ui-gallery__row--icons {
  align-items: stretch;
}

.dev-ui-gallery__nav-row {
  display: grid;
  gap: var(--ds-space-xs);
  max-inline-size: 300px;
}

.dev-ui-gallery__surface {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  min-inline-size: 0;
  padding: var(--ds-space-md);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: 8px;
  overflow: auto;
}

.dev-ui-gallery__surface--chat {
  align-items: flex-start;
  max-block-size: 720px;
}

.dev-ui-gallery__surface--agent {
  max-block-size: 720px;
}

.dev-ui-gallery__option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-inline-size: 0;
}

.dev-ui-gallery__option small {
  color: var(--ds-color-text-grey);
}

.dev-ui-gallery__menu-anchor {
  display: inline-flex;
  position: relative;
}

.dev-ui-gallery__menu-preview {
  position: static;
  inline-size: min(100%, 280px);
  animation: none;
}

.dev-ui-gallery__context-target {
  display: flex;
  align-items: center;
  justify-content: center;
  min-block-size: 96px;
  padding: var(--ds-space-lg);
  background: var(--ds-color-panel-main-bg);
  border: 1px dashed var(--ds-color-border-2);
  border-radius: 8px;
  color: var(--ds-color-secondary-text);
  font-size: var(--ds-font-size-label);
  outline: none;
}

.dev-ui-gallery__context-target:focus-visible {
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 2px var(--ds-color-primary-bg);
}

@media (max-width: 920px) {
  .dev-ui-gallery__grid--chat {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 780px) {
  .dev-ui-gallery {
    padding: var(--ds-space-lg);
  }

  .dev-ui-gallery__header,
  .dev-ui-gallery__section-heading {
    flex-direction: column;
    align-items: flex-start;
  }

  .dev-ui-gallery__sample--wide {
    grid-column: auto;
  }
}
</style>