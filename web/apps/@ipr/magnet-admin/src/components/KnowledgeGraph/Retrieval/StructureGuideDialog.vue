<template>
  <km-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <km-card class="px-lg py-sm dialog-card">
      <!-- Header -->
      <div class="km-card-section">
        <div class="cluster">
          <div class="flex-1 cluster gap-x-sm">
            <div>
              <div class="km-heading-7">Prompt Validation</div>
              <div class="km-description text-secondary-text">
                {{ hasErrors ? `${errorCount} issue${errorCount > 1 ? 's' : ''} found in template` : 'Template structure is valid' }}
              </div>
            </div>
          </div>
          <km-btn icon="close" flat round dense tone="weak" @click="$emit('update:modelValue', false)" />
        </div>
      </div>

      <!-- Content -->
      <div class="km-card-section pt-0 dialog-content">
        <div class="cluster" data-gap="md">
          <!-- Left: Validation Results -->
          <div class="basis-5">
            <div class="validation-panel">
              <div class="panel-header cluster mb-sm" data-justify="between">
                <span class="km-heading-8 text-weight-medium">Validation Results</span>
                <div class="status-badge" :class="hasErrors ? 'status-error' : 'status-success'">
                  <km-glyph :name="hasErrors ? 'error' : 'check'" size="18px" />
                  <span>{{ hasErrors ? `${errorCount} error${errorCount > 1 ? 's' : ''}` : 'Valid' }}</span>
                </div>
              </div>

              <div class="errors-container">
                <template v-if="hasErrors">
                  <TransitionGroup name="error-slide">
                    <div v-for="(error, idx) in validationErrors" :key="idx" class="error-item" :style="{ animationDelay: `${idx * 50}ms` }">
                      <div class="error-stripe" :class="getErrorTypeClass(error.type)" />
                      <div class="error-body">
                        <div class="cluster mb-xs gap-x-xs">
                          <km-badge :tone="getErrorBadgeTone(error.type)" :label="getErrorTypeLabel(error.type)" class="error-type-badge" />
                          <span v-if="error.section" class="section-tag">{{ formatSectionName(error.section) }}</span>
                        </div>
                        <div class="error-message">{{ error.message }}</div>
                        <div v-if="error.details" class="error-details mt-xs">
                          <pre>{{ error.details }}</pre>
                        </div>
                      </div>
                    </div>
                  </TransitionGroup>
                </template>

                <template v-else>
                  <div class="success-state">
                    <div class="success-icon-wrapper">
                      <km-glyph name="check" size="48px" tone="success" class="success-icon" />
                    </div>
                    <div class="km-heading-8 mt-md">All Checks Passed</div>
                    <div class="km-description text-secondary-text mt-xs">Your prompt template structure is valid and ready to use.</div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Right: Template Preview -->
          <div class="basis-7">
            <div class="preview-panel">
              <div class="panel-header cluster mb-sm" data-justify="between">
                <span class="km-heading-8 text-weight-medium">Template Preview</span>
                <km-btn icon="copy" flat dense size="sm" tone="weak" tooltip="Copy to clipboard" @click="copyTemplate" />
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
      </div>

      <!-- Footer -->
      <div class="km-card-actions p-md">
        <div class="km-space" />
        <km-btn :label="m.common_close()" flat tone="brand" @click="$emit('update:modelValue', false)" />
      </div>
    </km-card>
  </km-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import type { ValidationError } from './promptConfigConverter'
import { useNotify } from '@/composables/useNotify'

const props = defineProps<{
  modelValue: boolean
  validationErrors?: ValidationError[]
  promptText?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const { notifyCopied } = useNotify()

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

function getErrorBadgeTone(type: ValidationError['type']): string {
  const tones: Record<string, string> = {
    missing_section: 'danger',
    invalid_section: 'warning',
    parse_error: 'context',
    incompatible: 'info',
    not_found: 'neutral-strong',
  }
  return tones[type] || 'neutral-strong'
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
  notifyCopied('Copied to clipboard')
}
</script>

<style scoped>
.dialog-card {
  min-inline-size: 900px;
  max-inline-size: 1000px;
  max-block-size: 90vb;
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
  block-size: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding-block-end: 8px;
  block-size: 32px;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  margin-inline-end: 24px;
  border-radius: var(--ds-radius-full);
  font-size: var(--ds-font-size-caption);
  font-weight: 600;
}

.status-error {
  background: var(--ds-color-error-bg);
  color: var(--ds-color-error-text);
  border: 1px solid var(--ds-color-error-bg);
}

.status-success {
  background: var(--ds-color-success);
  color: var(--ds-color-success-text);
  border: 1px solid var(--ds-color-success);
}

/* Errors Container */
.errors-container {
  flex: 1;
  overflow-block: auto;
  max-block-size: 420px;
  padding-inline-end: 16px;
}

.error-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-block-end: 8px;
  background: var(--ds-color-background);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  animation: slide-in 0.3s ease forwards;
  opacity: 0;
  transform: translateY(-8px);
}

@keyframes slide-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-stripe {
  inline-size: 4px;
  border-radius: var(--ds-radius-xs);
  flex-shrink: 0;
  align-self: stretch;
}

.stripe-error {
  background: var(--ds-color-error);
}

.stripe-warning {
  background: var(--ds-color-warning);
}

.stripe-purple {
  background: var(--ds-color-secondary);
}

.stripe-info {
  background: var(--ds-color-info);
}

.stripe-grey {
  background: var(--ds-color-icon);
}

.error-body {
  flex: 1;
  min-inline-size: 0;
}

.error-type-badge {
  font-size: var(--ds-font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.section-tag {
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-label);
  padding: 2px 6px;
  background: var(--ds-color-light);
  border-radius: var(--ds-radius-sm);
  font-family: var(--ds-font-mono);
}

.error-message {
  font-size: var(--ds-font-size-label);
  line-height: 1.4;
  color: var(--ds-color-black);
}

.error-details {
  display: flex;
  align-items: flex-start;
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-error-text);
  padding: 0 8px;
  margin-block-start: 10px;
  background: var(--ds-color-warning-bg);
  border: 1px solid var(--ds-color-warning);
  border-radius: var(--ds-radius-sm);
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
  animation: bounce-in 0.4s ease;
}

@keyframes bounce-in {
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
  background: var(--ds-color-background);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  max-block-size: 420px;
  overflow-block: auto;
}

.code-row {
  display: flex;
  align-items: stretch;
}

.code-row:first-child .line-number,
.code-row:first-child .code-content {
  padding-block-start: 12px;
}

.code-row:last-child .line-number,
.code-row:last-child .code-content {
  padding-block-end: 12px;
}

.code-row:hover {
  background-color: var(--ds-color-light);
}

.line-number {
  padding: 0 6px;
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-caption);
  line-height: 1.5;
  color: var(--ds-color-icon);
  text-align: end;
  min-inline-size: 32px;
  user-select: none;
  border-inline-end: 1px solid var(--ds-color-border);
  background: var(--ds-color-light);
  flex-shrink: 0;
}

.code-content {
  flex: 1;
  margin: 0;
  padding: 0 16px;
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-caption);
  line-height: 1.5;
  color: var(--ds-color-black);
  white-space: pre-wrap;
  overflow-wrap: break-word;
  background: transparent;
}

/* Footer hint code */
code {
  padding: 2px 6px;
  background: var(--ds-color-light);
  border-radius: var(--ds-radius-sm);
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-label);
}

/* Transitions */
.error-slide-enter-active,
.error-slide-leave-active {
  transition:
    opacity var(--ds-duration-slow) var(--ds-ease-out),
    transform var(--ds-duration-slow) var(--ds-ease-out);
}

.error-slide-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}

.error-slide-leave-to {
  opacity: 0;
  transform: translateX(12px);
}

</style>
