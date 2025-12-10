<template>
  <div class="row items-center q-gutter-x-sm no-wrap">
    <!-- Variant selector -->
    <div class="bg-grey-2 row items-center no-wrap" style="border-radius: 4px">
      <!-- Inline validation indicator near the selected variant -->
      <q-btn
        v-if="validationErrors.length > 0"
        flat
        dense
        no-caps
        color="negative"
        icon="error"
        class="variant-group-btn q-px-8"
        @click="showStructureGuide = true"
      >
        <q-tooltip>Prompt template is invalid</q-tooltip>
      </q-btn>
      <q-btn-dropdown
        flat
        dense
        no-caps
        class="variant-selector variant-group-btn q-pl-12"
        :label="currentVariantLabel"
        dropdown-icon="expand_more"
        content-class="variant-dropdown-menu"
      >
        <q-list class="variant-dropdown-list">
          <div class="variant-dropdown-header">
            <q-icon name="tune" size="16px" class="q-mr-sm text-secondary-text" />
            <span>Prompt Variants</span>
          </div>
          <q-separator class="q-my-xs" />
          <!-- Custom rendering to add separator after base variant -->
          <template v-for="(variant, idx) in availableVariants" :key="variant.name">
            <q-item
              v-close-popup
              clickable
              class="variant-dropdown-item"
              :class="{ 'variant-active': variant.name === currentVariant }"
              @click="$emit('switch-variant', variant.name)"
            >
              <q-item-section avatar class="variant-icon-section">
                <div class="variant-icon-wrapper" :class="{ 'variant-icon-active': variant.name === currentVariant }">
                  <q-icon :name="variant.name === BASE_VARIANT_NAME ? 'home' : 'tune'" size="16px" />
                </div>
              </q-item-section>
              <q-item-section>
                <q-item-label class="variant-label">{{ variant.label }}</q-item-label>
                <q-item-label class="variant-caption">{{ variant.description }}</q-item-label>
              </q-item-section>
              <q-item-section v-if="variant.name === currentVariant" side>
                <q-icon name="check_circle" color="primary" size="18px" />
              </q-item-section>
            </q-item>
            <!-- Insert separator after base variant if it is not the last element -->
            <q-separator
              v-if="variant.name === BASE_VARIANT_NAME && availableVariants.length > 1 && idx !== availableVariants.length - 1"
              class="q-my-xs"
            />
          </template>
        </q-list>
      </q-btn-dropdown>
      <q-separator vertical color="grey-4" />
      <!-- Open prompt variant -->
      <q-btn flat dense icon="open_in_new" class="open-variant-btn variant-group-btn q-px-8" @click="$emit('open-variant')">
        <q-tooltip>Open prompt variant</q-tooltip>
      </q-btn>
    </div>

    <!-- Save button (Simple - only variant selection changed) -->
    <q-btn
      v-if="!isModified"
      no-caps
      unelevated
      color="primary"
      class="q-px-12"
      style="font-size: 13px; height: 36px"
      :loading="saving"
      label="Save"
      :disable="!hasUnsavedChanges"
      @click="$emit('save-current')"
    />

    <!-- Save dropdown (Configuration modified) -->
    <q-btn-dropdown
      v-else
      split
      color="primary"
      :loading="saving"
      :label="isBaseVariant ? 'Save as New' : 'Save'"
      :disable="!hasUnsavedChanges"
      content-class="save-dropdown-menu"
      @click="handleSavePrimaryAction"
    >
      <q-list class="save-dropdown-list">
        <div class="save-dropdown-header">
          <q-icon name="save_alt" size="16px" class="q-mr-sm" />
          <span>Save Options</span>
        </div>
        <q-separator class="q-my-xs" />

        <!-- Option 1: Save to Current / Base -->
        <q-item v-close-popup clickable class="save-dropdown-item" :disable="!hasUnsavedChanges" @click="handleSaveToCurrent">
          <q-item-section avatar class="save-icon-section">
            <div class="save-icon-wrapper save-icon-current">
              <q-icon :name="isBaseVariant ? 'warning' : 'save'" size="16px" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="save-label">{{ isBaseVariant ? 'Change Base Variant' : 'Save' }}</q-item-label>
            <q-item-label class="save-caption">
              {{ isBaseVariant ? 'Update the base prompt template' : 'Save changes to selected variant' }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <!-- Option 2: Create New Variant -->
        <q-item v-close-popup clickable class="save-dropdown-item" @click="showNewVariantDialog = true">
          <q-item-section avatar class="save-icon-section">
            <div class="save-icon-wrapper save-icon-new">
              <q-icon name="add" size="16px" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="save-label">Save as New</q-item-label>
            <q-item-label class="save-caption">Create a new prompt template variant</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-btn-dropdown>

    <!-- New Variant Dialog -->
    <q-dialog v-model="showNewVariantDialog" @before-show="initializeNewVariantForm">
      <q-card class="q-px-lg q-py-sm" style="min-width: 500px; max-width: 600px">
        <q-card-section>
          <div class="row items-center">
            <div class="col">
              <div class="km-heading-7">Create New Variant</div>
            </div>
            <div class="col-auto">
              <q-btn v-close-popup icon="close" flat dense />
            </div>
          </div>
        </q-card-section>

        <q-card-section>
          <div class="text-caption text-grey-7 q-mb-lg">Create a new prompt template variant based on your current retrieval configuration.</div>

          <div class="column q-gutter-y-lg">
            <div>
              <div class="km-input-label q-pb-sm">Display Name</div>
              <km-input
                placeholder="e.g., Custom Variant 1"
                :model-value="newVariantDisplayName"
                :rules="[(v) => !!v || 'Display name is required']"
                @update:model-value="onDisplayNameChange"
              />
            </div>

            <div>
              <div class="km-input-label q-pb-sm">Description</div>
              <km-input
                type="textarea"
                :rows="3"
                placeholder="Description..."
                :model-value="newVariantDescription"
                @update:model-value="newVariantDescription = $event"
              />
            </div>
          </div>
        </q-card-section>

        <q-card-actions class="q-py-lg q-px-md" align="right">
          <km-btn v-close-popup label="Cancel" flat color="primary" />
          <q-space />
          <km-btn label="Create & Save" :disable="!isValidVariantName" @click="saveAsNewVariant" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Save to Base Confirmation Dialog -->
    <q-dialog v-model="showSaveToBaseConfirm">
      <q-card class="q-px-lg q-py-sm" style="min-width: 500px; max-width: 600px">
        <q-card-section>
          <div class="row items-center">
            <div class="col row items-center q-gutter-x-sm">
              <div class="km-heading-7">Are you sure you want to proceed?</div>
            </div>
            <div class="col-auto">
              <q-btn v-close-popup icon="close" flat dense />
            </div>
          </div>
        </q-card-section>

        <q-card-section>
          <div class="text-body2 q-mb-md">
            You are about to update the
            <strong>Base Variant.</strong>
          </div>

          <div class="bg-yellow-1 q-pa-md rounded-borders text-grey-9 q-mb-md" style="border: 1px solid var(--q-warning)">
            <div class="row items-start no-wrap">
              <q-icon name="warning" color="yellow-8" size="26px" class="q-mr-sm q-mt-xs" />
              <div style="font-size: 13px; line-height: 1.4">
                This change will affect
                <strong>all knowledge graphs</strong>
                that use the default configuration and do not have a specific variant selected.
              </div>
            </div>
          </div>
        </q-card-section>

        <q-card-actions class="q-py-lg q-px-md" align="right">
          <km-btn v-close-popup label="Cancel" flat color="primary" />
          <q-space />
          <km-btn v-close-popup label="Update Base Variant" @click="$emit('save-current')" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Structure Guide Dialog -->
    <StructureGuideDialog v-model="showStructureGuide" :validation-errors="validationErrors" :prompt-text="currentPromptText" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
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
  const defaultDisplayName = props.graphName ? `Variant for ${props.graphName} retrieval agent` : 'New Variant'
  newVariantDisplayName.value = defaultDisplayName
  // Convert to snake_case for internal name
  newVariantName.value = defaultDisplayName
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
  // Prefill description
  newVariantDescription.value = props.graphName
    ? `Generated from retrieval configuration of knowledge graph ${props.graphName}`
    : 'Generated from retrieval configuration'
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
</script>

<style scoped>
/* Variant Group Button Height */
.variant-group-btn {
  height: 38px;
  min-height: 38px;
}

/* Variant Dropdown Styles */
.variant-selector {
  font-size: 13px;
  font-weight: 500;
}

.variant-selector :deep(.q-btn-dropdown__arrow) {
  transition: transform 0.2s ease;
}

/* Remove hover radius from the right side of variant selector */
.variant-selector :deep(.q-focus-helper) {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

/* Remove hover radius from the left side of open variant button */
.open-variant-btn :deep(.q-focus-helper) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}
</style>

<style>
/* Variant Dropdown Menu - Global styles for portal-rendered content */
.variant-dropdown-menu {
  border-radius: 8px;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-width: 240px;
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
  color: #6b7280;
}

.variant-dropdown-item {
  padding: 10px 16px;
  margin: 2px 6px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.variant-dropdown-item:hover {
  background-color: #f3f4f6;
}

.variant-dropdown-item.variant-active {
  background-color: #eff6ff;
}

.variant-dropdown-item.variant-active:hover {
  background-color: #dbeafe;
}

.variant-icon-section {
  min-width: 32px !important;
}

.variant-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background-color: #f3f4f6;
  color: #6b7280;
  transition: all 0.15s ease;
}

.variant-dropdown-item:hover .variant-icon-wrapper {
  background-color: #e5e7eb;
}

.variant-icon-wrapper.variant-icon-active {
  background-color: #dbeafe;
  color: #2563eb;
}

.variant-label {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.3;
}

.variant-caption {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
  line-height: 1.3;
}

.variant-active .variant-label {
  color: #1d4ed8;
}

/* Save Dropdown Menu Styles */
.save-dropdown-menu {
  border-radius: 8px;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-width: 240px;
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
  color: #6b7280;
}

.save-dropdown-item {
  padding: 10px 16px;
  margin: 2px 6px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.save-dropdown-item:hover {
  background-color: #f3f4f6;
}

.save-dropdown-item.disabled {
  opacity: 0.5;
}

.save-icon-section {
  min-width: 32px !important;
}

.save-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.save-icon-current {
  background-color: #dbeafe;
  color: #2563eb;
}

.save-dropdown-item:hover .save-icon-current {
  background-color: #bfdbfe;
}

.save-icon-new {
  background-color: #d1fae5;
  color: #059669;
}

.save-dropdown-item:hover .save-icon-new {
  background-color: #a7f3d0;
}

.save-label {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.3;
}

.save-caption {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
  line-height: 1.3;
}
</style>
