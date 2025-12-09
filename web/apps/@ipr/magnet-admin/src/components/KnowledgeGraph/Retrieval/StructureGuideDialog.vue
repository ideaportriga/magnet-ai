<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="q-px-lg q-py-sm dialog-card">
      <!-- Header -->
      <q-card-section>
        <div class="row items-center">
          <div class="col row items-center q-gutter-x-sm">
            <div>
              <div class="km-heading-7">Prompt Validation</div>
              <div class="km-description text-secondary-text">
                {{ hasErrors ? `${errorCount} issue${errorCount > 1 ? 's' : ''} found in template` : 'Template structure is valid' }}
              </div>
            </div>
          </div>
          <q-btn icon="close" flat round dense color="grey-6" @click="$emit('update:modelValue', false)" />
        </div>
      </q-card-section>

      <!-- Content -->
      <q-card-section class="q-pt-none dialog-content">
        <div class="row q-col-gutter-md">
          <!-- Left: Validation Results -->
          <div class="col-5">
            <div class="validation-panel">
              <div class="panel-header row items-center justify-between q-mb-sm">
                <span class="km-heading-8 text-weight-medium">Validation Results</span>
                <div class="status-badge" :class="hasErrors ? 'status-error' : 'status-success'">
                  <q-icon :name="hasErrors ? 'error' : 'check_circle'" size="18px" />
                  <span>{{ hasErrors ? `${errorCount} error${errorCount > 1 ? 's' : ''}` : 'Valid' }}</span>
                </div>
              </div>

              <div class="errors-container">
                <template v-if="hasErrors">
                  <TransitionGroup name="error-slide">
                    <div v-for="(error, idx) in validationErrors" :key="idx" class="error-item" :style="{ animationDelay: `${idx * 50}ms` }">
                      <div class="error-stripe" :class="getErrorTypeClass(error.type)" />
                      <div class="error-body">
                        <div class="row items-center q-gutter-x-xs q-mb-xs">
                          <q-badge :color="getErrorBadgeColor(error.type)" :label="getErrorTypeLabel(error.type)" class="error-type-badge" />
                          <span v-if="error.section" class="section-tag">{{ formatSectionName(error.section) }}</span>
                        </div>
                        <div class="error-message">{{ error.message }}</div>
                        <div v-if="error.details" class="error-details q-mt-xs">
                          <pre>{{ error.details }}</pre>
                        </div>
                      </div>
                    </div>
                  </TransitionGroup>
                </template>

                <template v-else>
                  <div class="success-state">
                    <div class="success-icon-wrapper">
                      <q-icon name="check_circle" size="48px" color="positive" class="success-icon" />
                    </div>
                    <div class="km-heading-8 q-mt-md">All Checks Passed</div>
                    <div class="km-description text-secondary-text q-mt-xs">Your prompt template structure is valid and ready to use.</div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Right: Template Preview -->
          <div class="col-7">
            <div class="preview-panel">
              <div class="panel-header row items-center justify-between q-mb-sm">
                <span class="km-heading-8 text-weight-medium">Template Preview</span>
                <q-btn icon="content_copy" flat dense size="sm" color="grey-7" @click="copyTemplate">
                  <q-tooltip>Copy to clipboard</q-tooltip>
                </q-btn>
              </div>

              <div class="code-preview">
                <div v-for="(line, idx) in lines" :key="idx" class="code-row">
                  <div class="line-number">{{ idx + 1 }}</div>
                  <div class="code-content">{{ line || ' ' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </q-card-section>

      <!-- Footer -->
      <q-card-actions class="q-pa-md">
        <q-space />
        <km-btn label="Close" flat color="primary" @click="$emit('update:modelValue', false)" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar'
import { computed } from 'vue'
import type { ValidationError } from './promptConfigConverter'

const props = defineProps<{
  modelValue: boolean
  validationErrors?: ValidationError[]
  promptText?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const $q = useQuasar()

const hasErrors = computed(() => (props.validationErrors?.length ?? 0) > 0)
const errorCount = computed(() => props.validationErrors?.length ?? 0)

const lines = computed(() => {
  if (!props.promptText) return ['No prompt template provided']
  return props.promptText.split('\n')
})

function getErrorTypeClass(type: ValidationError['type']): string {
  const classes: Record<string, string> = {
    missing_section: 'stripe-error',
    invalid_section: 'stripe-warning',
    parse_error: 'stripe-purple',
    incompatible: 'stripe-info',
    not_found: 'stripe-grey',
  }
  return classes[type] || 'stripe-grey'
}

function getErrorBadgeColor(type: ValidationError['type']): string {
  const colors: Record<string, string> = {
    missing_section: 'negative',
    invalid_section: 'warning',
    parse_error: 'purple-6',
    incompatible: 'info',
    not_found: 'grey-6',
  }
  return colors[type] || 'grey-6'
}

function getErrorTypeLabel(type: ValidationError['type']): string {
  const labels: Record<string, string> = {
    missing_section: 'Missing',
    invalid_section: 'Invalid',
    parse_error: 'Parse Error',
    incompatible: 'Incompatible',
    not_found: 'Not Found',
  }
  return labels[type] || 'Error'
}

function formatSectionName(section: string): string {
  return section
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function copyTemplate() {
  if (!props.promptText) return
  navigator.clipboard.writeText(props.promptText)
  $q.notify({
    type: 'positive',
    message: 'Copied to clipboard',
    position: 'bottom',
    timeout: 1500,
  })
}
</script>

<style scoped>
.dialog-card {
  min-width: 900px;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-content {
  flex: 1;
  overflow: hidden;
}

/* Panels */
.validation-panel,
.preview-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding-bottom: 8px;
  height: 32px;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  margin-right: 24px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.status-error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.status-success {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

/* Errors Container */
.errors-container {
  flex: 1;
  overflow-y: auto;
  max-height: 420px;
  padding-right: 16px;
}

.error-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  animation: slideIn 0.3s ease forwards;
  opacity: 0;
  transform: translateY(-8px);
}

@keyframes slideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-stripe {
  width: 4px;
  border-radius: 2px;
  flex-shrink: 0;
  align-self: stretch;
}

.stripe-error {
  background: var(--q-negative);
}

.stripe-warning {
  background: var(--q-warning);
}

.stripe-purple {
  background: #9c27b0;
}

.stripe-info {
  background: var(--q-info);
}

.stripe-grey {
  background: #9e9e9e;
}

.error-body {
  flex: 1;
  min-width: 0;
}

.error-type-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.section-tag {
  font-size: 11px;
  color: #666;
  padding: 2px 6px;
  background: #eee;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.error-message {
  font-size: 13px;
  line-height: 1.4;
  color: #333;
}

.error-details {
  display: flex;
  align-items: flex-start;
  font-size: 11px;
  color: #9a3412;
  padding: 0 8px;
  margin-top: 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 4px;
}

.error-details pre {
  margin: 5px 0;
}

/* Success State */
.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.success-icon-wrapper {
  position: relative;
}

.success-icon {
  animation: bounceIn 0.4s ease;
}

@keyframes bounceIn {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  60% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Code Preview */
.code-preview {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  max-height: 420px;
  overflow-y: auto;
}

.code-row {
  display: flex;
  align-items: stretch;
}

.code-row:first-child .line-number,
.code-row:first-child .code-content {
  padding-top: 12px;
}

.code-row:last-child .line-number,
.code-row:last-child .code-content {
  padding-bottom: 12px;
}

.code-row:hover {
  background-color: #f1f2f3;
}

.line-number {
  padding: 0 6px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #999;
  text-align: right;
  min-width: 32px;
  user-select: none;
  border-right: 1px solid #e8e8e8;
  background: #f0f1f2;
  flex-shrink: 0;
}

.code-content {
  flex: 1;
  margin: 0;
  padding: 0 16px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
  background: transparent;
}

/* Footer hint code */
code {
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  color: #666;
}

/* Transitions */
.error-slide-enter-active,
.error-slide-leave-active {
  transition: all 0.25s ease;
}

.error-slide-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}

.error-slide-leave-to {
  opacity: 0;
  transform: translateX(12px);
}

/* Scrollbar */
.errors-container::-webkit-scrollbar,
.code-preview::-webkit-scrollbar {
  width: 6px;
}

.errors-container::-webkit-scrollbar-track,
.code-preview::-webkit-scrollbar-track {
  background: transparent;
}

.errors-container::-webkit-scrollbar-thumb,
.code-preview::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

.errors-container::-webkit-scrollbar-thumb:hover,
.code-preview::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}
</style>
