<template>
  <km-card flat bordered class="tool-card cursor-pointer" :class="[variantClass, { 'tool-disabled': disabled }]" @click="$emit('click')">
    <div class="km-card-section p-sm pl-md pr-md">
      <div class="cluster gap-x-sm" data-align="start">
        <!-- Icon -->
        <div class="flex" style="flex-direction: column; justify-content: center; block-size: 42px">
          <km-avatar :icon="icon" :tone="avatarTone" size="32px" font-size="18px" />
        </div>

        <!-- Content -->
        <div class="flex-1">
          <div class="cluster gap-x-sm">
            <div class="km-heading-8 text-weight-medium">{{ label }}</div>
            <km-badge v-if="badge" tone="warning" :label="badge" class="text-weight-medium" />
          </div>
          <div class="mt-2xs text-secondary-text km-body-sm">{{ description || 'No description configured' }}</div>

          <!-- Stats Slot -->
          <div v-if="$slots.stats" class="cluster gap-x-md mt-xs">
            <slot name="stats" />
          </div>
        </div>

        <!-- Toggle (optional) -->
        <div v-if="showToggle" class="flex-none self-center">
          <km-toggle :model-value="enabled" dense :disable="toggleDisabled" @click.stop @update:model-value="$emit('update:enabled', $event)" />
        </div>
      </div>
    </div>
  </km-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

export interface ToolCardProps {
  icon: string
  label: string
  description?: string
  variant: 'search' | 'exit'
  badge?: string
  showToggle?: boolean
  enabled?: boolean
  toggleDisabled?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<ToolCardProps>(), {
  description: '',
  badge: '',
  showToggle: false,
  enabled: false,
  toggleDisabled: false,
  disabled: false,
})

defineEmits<{
  (e: 'click'): void
  (e: 'update:enabled', value: boolean): void
}>()

const variantClass = computed(() => `tool-card--${props.variant}`)
const avatarTone = computed(() => props.variant === 'exit' ? 'danger-soft' : 'brand-soft')
</script>

<style scoped>
.tool-card {
  border-radius: var(--ds-radius-md);
  transition: var(--ds-transition-colors), var(--ds-transition-shadow), var(--ds-transition-transform);
}

/* Search Tool Cards (Filter & Retrieval) */
.tool-card--search {
  border-color: var(--ds-color-border-2);
  background: linear-gradient(135deg, var(--ds-color-primary-bg) 0%, var(--ds-color-white) 100%);
}

.tool-card--search:hover {
  border-color: var(--ds-color-primary);
}

.tool-card--search.tool-disabled {
  background: linear-gradient(135deg, var(--ds-color-background) 0%, var(--ds-color-white) 100%);
  border-color: var(--ds-color-border);
}

.tool-card--search.tool-disabled:hover {
  border-color: var(--ds-color-border-2);
}

/* Exit Tool Cards */
.tool-card--exit {
  border-color: var(--ds-color-error-bg);
  background: linear-gradient(135deg, var(--ds-color-error-bg) 0%, var(--ds-color-white) 100%);
}

.tool-card--exit:hover {
  border-color: var(--ds-color-error);
}

/* Disabled state for all variants */
.tool-disabled {
  opacity: 0.5;
  pointer-events: auto;
}
</style>
