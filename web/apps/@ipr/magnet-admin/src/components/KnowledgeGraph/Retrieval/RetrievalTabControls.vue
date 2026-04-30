<template>
  <div class="cluster gap-x-sm" data-wrap="no">
    <!-- Variant selector -->
    <div class="bg-grey-2 cluster" data-wrap="no" style="border-radius: var(--ds-radius-sm)">
      <!-- Inline validation indicator near the selected variant -->
      <km-btn
        v-if="validationErrors.length > 0"
        flat
        dense
        no-caps
        tone="danger"
        icon="error"
        class="variant-group-btn px-sm"
        @click="showStructureGuide = true"
      >
        <km-tooltip>{{ m.knowledgeGraph_promptTemplateInvalid() }}</km-tooltip>
      </km-btn>
      <km-btn-dropdown
        flat
        dense
        no-caps
        class="variant-selector variant-group-btn pl-md"
        :label="currentVariantLabel"
        dropdown-icon="chevron-down"
        content-class="variant-dropdown-menu"
      >
        <ul class="km-list variant-dropdown-list">
          <div class="variant-dropdown-header">
            <km-glyph name="tune" size="16px" class="mr-sm text-secondary-text" />
            <span>{{ m.knowledgeGraph_promptVariants() }}</span>
          </div>
          <km-separator class="my-xs" />
          <!-- Custom rendering to add separator after base variant -->
          <template v-for="(variant, idx) in availableVariants" :key="variant.name">
            <li
              class="km-item variant-dropdown-item"
              clickable
              :class="{ 'variant-active': variant.name === currentVariant }"
              @click="$emit('switch-variant', variant.name)"
            >
              <div class="km-item-section variant-icon-section" avatar>
                <div class="variant-icon-wrapper" :class="{ 'variant-icon-active': variant.name === currentVariant }">
                  <km-glyph :name="variant.name === BASE_VARIANT_NAME ? 'home' : 'tune'" size="16px" />
                </div>
              </div>
              <div class="km-item-section">
                <span class="km-item-label variant-label">{{ variant.label }}</span>
                <span class="km-item-label variant-caption">{{ variant.description }}</span>
              </div>
              <div v-if="variant.name === currentVariant" class="km-item-section" side>
                <km-glyph name="check" tone="brand" size="18px" />
              </div>
            </li>
            <!-- Insert separator after base variant if it is not the last element -->
            <km-separator
              v-if="variant.name === BASE_VARIANT_NAME && availableVariants.length > 1 && idx !== availableVariants.length - 1"
              class="my-xs"
            />
          </template>
        </ul>
      </km-btn-dropdown>
      <km-separator vertical tone="subtle" />
      <!-- Open prompt variant -->
      <km-btn flat dense icon="external-link" class="open-variant-btn variant-group-btn px-sm" :tooltip="m.knowledgeGraph_openPromptVariant()" @click="$emit('open-variant')" />
    </div>

    <!-- Save button (Simple - only variant selection changed) -->
    <km-btn
      v-if="!isModified"
      no-caps
      unelevated
      class="px-md km-body-sm"
      style="block-size: 36px"
      :loading="saving"
      :label="m.common_save()"
      :disable="!hasUnsavedChanges"
      @click="$emit('save-current')"
    />

    <!-- Save dropdown (Configuration modified) -->
    <km-btn-dropdown
      v-else
      split
      :loading="saving"
      :label="isBaseVariant ? m.knowledgeGraph_saveAsNew() : m.common_save()"
      :disable="!hasUnsavedChanges"
      content-class="save-dropdown-menu"
      @click="handleSavePrimaryAction"
    >
      <ul class="km-list save-dropdown-list">
        <div class="save-dropdown-header">
          <km-glyph name="save_alt" size="16px" class="mr-sm" />
          <span>{{ m.knowledgeGraph_saveOptions() }}</span>
        </div>
        <km-separator class="my-xs" />

        <!-- Option 1: Save to Current / Base -->
        <li class="km-item save-dropdown-item" clickable :disable="!hasUnsavedChanges" @click="handleSaveToCurrent">
          <div class="km-item-section save-icon-section" avatar>
            <div class="save-icon-wrapper save-icon-current">
              <km-glyph :name="isBaseVariant ? 'warning' : 'save'" size="16px" />
            </div>
          </div>
          <div class="km-item-section">
            <span class="km-item-label save-label">{{ isBaseVariant ? m.knowledgeGraph_changeBaseVariant() : m.common_save() }}</span>
            <span class="km-item-label save-caption">
              {{ isBaseVariant ? m.knowledgeGraph_updateBasePromptTemplate() : m.knowledgeGraph_saveChangesToVariant() }}
            </span>
          </div>
        </li>

        <!-- Option 2: Create New Variant -->
        <li class="km-item save-dropdown-item" clickable @click="showNewVariantDialog = true">
          <div class="km-item-section save-icon-section" avatar>
            <div class="save-icon-wrapper save-icon-new">
              <km-glyph name="add" size="16px" />
            </div>
          </div>
          <div class="km-item-section">
            <span class="km-item-label save-label">{{ m.knowledgeGraph_saveAsNew() }}</span>
            <span class="km-item-label save-caption">{{ m.knowledgeGraph_createNewVariantCaption() }}</span>
          </div>
        </li>
      </ul>
    </km-btn-dropdown>

    <!-- New Variant Dialog -->
    <km-dialog v-model="showNewVariantDialog" @before-show="initializeNewVariantForm">
      <km-card class="px-lg py-sm" style="min-inline-size: 500px; max-inline-size: 600px">
        <div class="km-card-section">
          <div class="cluster">
            <div class="flex-1">
              <div class="km-heading-7">{{ m.knowledgeGraph_createNewVariant() }}</div>
            </div>
            <div class="flex-none">
              <km-btn icon="close" flat dense @click="showNewVariantDialog = false" />
            </div>
          </div>
        </div>

        <div class="km-card-section">
          <div class="text-caption text-grey-7 mb-lg">{{ m.knowledgeGraph_createNewVariantDesc() }}</div>

          <div class="stack gap-y-lg">
            <div>
              <div class="km-input-label pb-sm">{{ m.common_displayName() }}</div>
              <km-input
                :placeholder="m.knowledgeGraph_variantNamePlaceholder()"
                :model-value="newVariantDisplayName"
                :rules="[(v) => !!v || m.knowledgeGraph_displayNameRequired()]"
                @update:model-value="onDisplayNameChange"
              />
            </div>

            <div>
              <div class="km-input-label pb-sm">{{ m.common_description() }}</div>
              <km-input
                type="textarea"
                :rows="3"
                :placeholder="m.common_descriptionPlaceholder()"
                :model-value="newVariantDescription"
                @update:model-value="newVariantDescription = $event"
              />
            </div>
          </div>
        </div>

        <div class="km-card-actions py-lg px-md" align="right">
          <km-btn :label="m.common_cancel()" flat tone="brand" @click="showNewVariantDialog = false" />
          <div class="km-space" />
          <km-btn :label="m.knowledgeGraph_createAndSave()" :disable="!isValidVariantName" @click="saveAsNewVariant" />
        </div>
      </km-card>
    </km-dialog>

    <!-- Save to Base Confirmation Dialog -->
    <km-dialog v-model="showSaveToBaseConfirm">
      <km-card class="px-lg py-sm" style="min-inline-size: 500px; max-inline-size: 600px">
        <div class="km-card-section">
          <div class="cluster">
            <div class="flex-1 cluster gap-x-sm">
              <div class="km-heading-7">{{ m.knowledgeGraph_confirmProceed() }}</div>
            </div>
            <div class="flex-none">
              <km-btn icon="close" flat dense @click="showSaveToBaseConfirm = false" />
            </div>
          </div>
        </div>

        <div class="km-card-section">
          <div class="text-body2 mb-md">
            {{ m.knowledgeGraph_aboutToUpdateThe() }}
            <strong>{{ m.knowledgeGraph_baseVariantDot() }}</strong>
          </div>

          <div class="bg-yellow-1 p-md rounded-borders text-grey-9 mb-md" style="border: 1px solid var(--ds-color-warning)">
            <div class="cluster" data-wrap="no" data-align="start">
              <km-glyph name="warning" tone="warning" size="26px" class="mr-sm mt-xs" />
              <div class="km-body-sm" style="line-height: 1.4">
                {{ m.knowledgeGraph_changeWillAffect() }}
                <strong>{{ m.knowledgeGraph_allKnowledgeGraphsLabel() }}</strong>
                {{ m.knowledgeGraph_thatUseDefaultConfig() }}
              </div>
            </div>
          </div>
        </div>

        <div class="km-card-actions py-lg px-md" align="right">
          <km-btn :label="m.common_cancel()" flat tone="brand" @click="showSaveToBaseConfirm = false" />
          <div class="km-space" />
          <km-btn :label="m.knowledgeGraph_updateBaseVariant()" @click="confirmSaveToBase" />
        </div>
      </km-card>
    </km-dialog>

    <!-- Structure Guide Dialog -->
    <StructureGuideDialog v-model="showStructureGuide" :validation-errors="validationErrors" :prompt-text="currentPromptText" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { m } from '@/paraglide/messages'
import StructureGuideDialog from './StructureGuideDialog.vue'
import { BASE_VARIANT_NAME, type ValidationError } from './promptConfigConverter'

const props = defineProps<{
  validationErrors: ValidationError[]
  availableVariants: Array<{ name: string; label: string; description: string }>
  currentVariant: string
  currentVariantLabel: string
  hasUnsavedChanges: boolean
  isModified: boolean
  saving: boolean
  currentPromptText: string
  graphName: string
}>()

const emit = defineEmits<{
  (e: 'switch-variant', variantName: string): void
  (e: 'open-variant'): void
  (e: 'save-current'): void
  (e: 'save-new', payload: { name: string; displayName: string; description: string }): void
}>()

const showNewVariantDialog = ref(false)
const showSaveToBaseConfirm = ref(false)
const showStructureGuide = ref(false)

const newVariantName = ref('')
const newVariantDisplayName = ref('')
const newVariantDescription = ref('')

const isBaseVariant = computed(() => props.currentVariant === BASE_VARIANT_NAME)

const isValidVariantName = computed(() => {
  return newVariantName.value && /^[a-z0-9_]+$/.test(newVariantName.value)
})

function handleSavePrimaryAction() {
  if (isBaseVariant.value && props.isModified) {
    showNewVariantDialog.value = true
  } else {
    emit('save-current')
  }
}

function handleSaveToCurrent() {
  if (isBaseVariant.value && props.isModified) {
    showSaveToBaseConfirm.value = true
  } else {
    emit('save-current')
  }
}

function initializeNewVariantForm() {
  // Prefill display name with graph name + " Variant"
  const defaultDisplayName = props.graphName ? m.knowledgeGraph_variantForGraph({ name: props.graphName }) : m.knowledgeGraph_newVariant()
  newVariantDisplayName.value = defaultDisplayName
  // Convert to snake_case for internal name
  newVariantName.value = defaultDisplayName
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
  // Prefill description
  newVariantDescription.value = props.graphName
    ? m.knowledgeGraph_variantDesc({ name: props.graphName })
    : m.knowledgeGraph_variantDescDefault()
}

function onDisplayNameChange(val: string) {
  newVariantDisplayName.value = val
  // Convert to snake_case: lowercase, replace spaces with underscores, remove special chars
  if (val) {
    newVariantName.value = val
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
  }
}

function saveAsNewVariant() {
  if (isValidVariantName.value) {
    emit('save-new', {
      name: newVariantName.value,
      displayName: newVariantDisplayName.value,
      description: newVariantDescription.value,
    })
    showNewVariantDialog.value = false
    newVariantName.value = ''
    newVariantDisplayName.value = ''
    newVariantDescription.value = ''
  }
}

function confirmSaveToBase() {
  showSaveToBaseConfirm.value = false
  emit('save-current')
}
</script>

<style scoped>
/* Variant Group Button Height */
.variant-group-btn {
  block-size: 38px;
  min-block-size: 38px;
}

/* Variant Dropdown Styles */
.variant-selector {
  font-size: var(--ds-font-size-label);
  font-weight: 500;
}

/* Remove hover radius from the right side of variant selector */
/* Remove hover radius from the left side of open variant button */
</style>

<style>
/* Variant Dropdown Menu - Global styles for portal-rendered content */
.variant-dropdown-menu {
  border-radius: var(--ds-radius-lg);
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--ds-color-border);
  overflow: hidden;
  min-inline-size: 240px;
}

.variant-dropdown-list {
  padding: 4px 0;
}

.variant-dropdown-header {
  display: flex;
  align-items: center;
  padding: 10px 16px 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ds-color-label);
}

.variant-dropdown-item {
  padding: 10px 16px;
  margin: 2px 6px;
  border-radius: var(--ds-radius-md);
  transition: var(--ds-transition-colors);
}

.variant-dropdown-item:hover {
  background-color: var(--ds-color-light);
}

.variant-dropdown-item.variant-active {
  background-color: var(--ds-color-primary-bg);
}

.variant-dropdown-item.variant-active:hover {
  background-color: var(--ds-color-primary-light);
}

.variant-icon-section {
  min-inline-size: 32px !important;
}

.variant-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 28px;
  block-size: 28px;
  border-radius: var(--ds-radius-md);
  background-color: var(--ds-color-light);
  color: var(--ds-color-label);
  transition: var(--ds-transition-colors);
}

.variant-dropdown-item:hover .variant-icon-wrapper {
  background-color: var(--ds-color-border);
}

.variant-icon-wrapper.variant-icon-active {
  background-color: var(--ds-color-primary-light);
  color: var(--ds-color-primary);
}

.variant-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--ds-color-black);
  line-height: 1.3;
}

.variant-caption {
  font-size: 11px;
  color: var(--ds-color-label);
  margin-block-start: 2px;
  line-height: 1.3;
}

.variant-active .variant-label {
  color: var(--ds-color-primary);
}

/* Save Dropdown Menu Styles */
.save-dropdown-menu {
  border-radius: var(--ds-radius-lg);
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--ds-color-border);
  overflow: hidden;
  min-inline-size: 240px;
}

.save-dropdown-list {
  padding: 4px 0;
}

.save-dropdown-header {
  display: flex;
  align-items: center;
  padding: 10px 16px 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ds-color-label);
}

.save-dropdown-item {
  padding: 10px 16px;
  margin: 2px 6px;
  border-radius: var(--ds-radius-md);
  transition: var(--ds-transition-colors);
}

.save-dropdown-item:hover {
  background-color: var(--ds-color-light);
}

.save-dropdown-item.disabled {
  opacity: 0.5;
}

.save-icon-section {
  min-inline-size: 32px !important;
}

.save-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 28px;
  block-size: 28px;
  border-radius: var(--ds-radius-md);
  transition: var(--ds-transition-colors);
}

.save-icon-current {
  background-color: var(--ds-color-primary-light);
  color: var(--ds-color-primary);
}

.save-dropdown-item:hover .save-icon-current {
  background-color: var(--ds-color-primary-bg);
}

.save-icon-new {
  background-color: var(--ds-color-success-text);
  color: var(--ds-color-success);
}

.save-dropdown-item:hover .save-icon-new {
  background-color: var(--ds-color-success-text);
}

.save-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--ds-color-black);
  line-height: 1.3;
}

.save-caption {
  font-size: 11px;
  color: var(--ds-color-label);
  margin-block-start: 2px;
  line-height: 1.3;
}
</style>
