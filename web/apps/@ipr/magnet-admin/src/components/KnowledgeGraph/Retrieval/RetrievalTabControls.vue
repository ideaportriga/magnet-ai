<template>
  <div class="row items-center q-gutter-x-sm no-wrap">
    <!-- Variant selector -->
    <div class="bg-grey-2 row items-center no-wrap" style="border-radius: var(--radius-sm)">
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
        <q-tooltip>{{ m.knowledgeGraph_promptTemplateInvalid() }}</q-tooltip>
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
            <span>{{ m.knowledgeGraph_promptVariants() }}</span>
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
        <q-tooltip>{{ m.knowledgeGraph_openPromptVariant() }}</q-tooltip>
      </q-btn>
    </div>

    <!-- Save button (Simple - only variant selection changed) -->
    <q-btn
      v-if="!isModified"
      no-caps
      unelevated
      color="primary"
      class="q-px-12 km-body-sm"
      style="height: 36px"
      :loading="saving"
      :label="m.common_save()"
      :disable="!hasUnsavedChanges"
      @click="$emit('save-current')"
    />

    <!-- Save dropdown (Configuration modified) -->
    <q-btn-dropdown
      v-else
      split
      color="primary"
      :loading="saving"
      :label="isBaseVariant ? m.knowledgeGraph_saveAsNew() : m.common_save()"
      :disable="!hasUnsavedChanges"
      content-class="save-dropdown-menu"
      @click="handleSavePrimaryAction"
    >
      <q-list class="save-dropdown-list">
        <div class="save-dropdown-header">
          <q-icon name="save_alt" size="16px" class="q-mr-sm" />
          <span>{{ m.knowledgeGraph_saveOptions() }}</span>
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
            <q-item-label class="save-label">{{ isBaseVariant ? m.knowledgeGraph_changeBaseVariant() : m.common_save() }}</q-item-label>
            <q-item-label class="save-caption">
              {{ isBaseVariant ? m.knowledgeGraph_updateBasePromptTemplate() : m.knowledgeGraph_saveChangesToVariant() }}
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
            <q-item-label class="save-label">{{ m.knowledgeGraph_saveAsNew() }}</q-item-label>
            <q-item-label class="save-caption">{{ m.knowledgeGraph_createNewVariantCaption() }}</q-item-label>
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
              <div class="km-heading-7">{{ m.knowledgeGraph_createNewVariant() }}</div>
            </div>
            <div class="col-auto">
              <q-btn v-close-popup icon="close" flat dense />
            </div>
          </div>
        </q-card-section>

        <q-card-section>
          <div class="text-caption text-grey-7 q-mb-lg">{{ m.knowledgeGraph_createNewVariantDesc() }}</div>

          <div class="column q-gutter-y-lg">
            <div>
              <div class="km-input-label q-pb-sm">{{ m.common_displayName() }}</div>
              <km-input
                :placeholder="m.knowledgeGraph_variantNamePlaceholder()"
                :model-value="newVariantDisplayName"
                :rules="[(v) => !!v || m.knowledgeGraph_displayNameRequired()]"
                @update:model-value="onDisplayNameChange"
              />
            </div>

            <div>
              <div class="km-input-label q-pb-sm">{{ m.common_description() }}</div>
              <km-input
                type="textarea"
                :rows="3"
                :placeholder="m.common_descriptionPlaceholder()"
                :model-value="newVariantDescription"
                @update:model-value="newVariantDescription = $event"
              />
            </div>
          </div>
        </q-card-section>

        <q-card-actions class="q-py-lg q-px-md" align="right">
          <km-btn v-close-popup :label="m.common_cancel()" flat color="primary" />
          <q-space />
          <km-btn :label="m.knowledgeGraph_createAndSave()" :disable="!isValidVariantName" @click="saveAsNewVariant" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Save to Base Confirmation Dialog -->
    <q-dialog v-model="showSaveToBaseConfirm">
      <q-card class="q-px-lg q-py-sm" style="min-width: 500px; max-width: 600px">
        <q-card-section>
          <div class="row items-center">
            <div class="col row items-center q-gutter-x-sm">
              <div class="km-heading-7">{{ m.knowledgeGraph_confirmProceed() }}</div>
            </div>
            <div class="col-auto">
              <q-btn v-close-popup icon="close" flat dense />
            </div>
          </div>
        </q-card-section>

        <q-card-section>
          <div class="text-body2 q-mb-md">
            {{ m.knowledgeGraph_aboutToUpdateThe() }}
            <strong>{{ m.knowledgeGraph_baseVariantDot() }}</strong>
          </div>

          <div class="bg-yellow-1 q-pa-md rounded-borders text-grey-9 q-mb-md" style="border: 1px solid var(--q-warning)">
            <div class="row items-start no-wrap">
              <q-icon name="warning" color="yellow-8" size="26px" class="q-mr-sm q-mt-xs" />
              <div class="km-body-sm" style="line-height: 1.4">
                {{ m.knowledgeGraph_changeWillAffect() }}
                <strong>{{ m.knowledgeGraph_allKnowledgeGraphsLabel() }}</strong>
                {{ m.knowledgeGraph_thatUseDefaultConfig() }}
              </div>
            </div>
          </div>
        </q-card-section>

        <q-card-actions class="q-py-lg q-px-md" align="right">
          <km-btn v-close-popup :label="m.common_cancel()" flat color="primary" />
          <q-space />
          <km-btn v-close-popup :label="m.knowledgeGraph_updateBaseVariant()" @click="$emit('save-current')" />
        </q-card-actions>
      </q-card>
    </q-dialog>

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
</script>

<style scoped>
/* Variant Group Button Height */
.variant-group-btn {
  height: 38px;
  min-height: 38px;
}

/* Variant Dropdown Styles */
.variant-selector {
  font-size: var(--km-font-size-label);
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
  border-radius: var(--radius-lg);
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--q-border);
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
  color: var(--q-label);
}

.variant-dropdown-item {
  padding: 10px 16px;
  margin: 2px 6px;
  border-radius: var(--radius-md);
  transition: all 0.15s ease;
}

.variant-dropdown-item:hover {
  background-color: var(--q-light);
}

.variant-dropdown-item.variant-active {
  background-color: var(--q-primary-bg);
}

.variant-dropdown-item.variant-active:hover {
  background-color: var(--q-primary-light);
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
  border-radius: var(--radius-md);
  background-color: var(--q-light);
  color: var(--q-label);
  transition: all 0.15s ease;
}

.variant-dropdown-item:hover .variant-icon-wrapper {
  background-color: var(--q-border);
}

.variant-icon-wrapper.variant-icon-active {
  background-color: var(--q-primary-light);
  color: var(--q-primary);
}

.variant-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--q-black);
  line-height: 1.3;
}

.variant-caption {
  font-size: 11px;
  color: var(--q-label);
  margin-top: 2px;
  line-height: 1.3;
}

.variant-active .variant-label {
  color: var(--q-primary);
}

/* Save Dropdown Menu Styles */
.save-dropdown-menu {
  border-radius: var(--radius-lg);
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--q-border);
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
  color: var(--q-label);
}

.save-dropdown-item {
  padding: 10px 16px;
  margin: 2px 6px;
  border-radius: var(--radius-md);
  transition: all 0.15s ease;
}

.save-dropdown-item:hover {
  background-color: var(--q-light);
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
  border-radius: var(--radius-md);
  transition: all 0.15s ease;
}

.save-icon-current {
  background-color: var(--q-primary-light);
  color: var(--q-primary);
}

.save-dropdown-item:hover .save-icon-current {
  background-color: var(--q-primary-bg);
}

.save-icon-new {
  background-color: var(--q-success-text);
  color: var(--q-success);
}

.save-dropdown-item:hover .save-icon-new {
  background-color: var(--q-success-text);
}

.save-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--q-black);
  line-height: 1.3;
}

.save-caption {
  font-size: 11px;
  color: var(--q-label);
  margin-top: 2px;
  line-height: 1.3;
}
</style>
