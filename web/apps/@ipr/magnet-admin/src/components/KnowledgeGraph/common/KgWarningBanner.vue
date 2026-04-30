<template>
  <div class="kg-warning-banner" :class="`kg-warning-banner--${variant}`">
    <km-glyph :name="iconName" :tone="iconTone" size="28px" class="mr-sm" />
    <div class="flex-1">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

type BannerVariant = 'warning' | 'error' | 'info' | 'neutral'

interface Props {
  variant?: BannerVariant
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'warning',
})

const variantConfig: Record<BannerVariant, { icon: string; iconTone: string }> = {
  warning: { icon: 'warning', iconTone: 'warning' },
  error: { icon: 'error', iconTone: 'danger' },
  info: { icon: 'info', iconTone: 'info' },
  neutral: { icon: 'info', iconTone: 'weak' },
}

const iconName = computed(() => props.icon || variantConfig[props.variant].icon)
const iconTone = computed(() => variantConfig[props.variant].iconTone)
</script>

<style scoped>
.kg-warning-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-label);
  line-height: 1.4;
}

.kg-warning-banner--warning {
  background: var(--ds-color-warning-bg);
  border: 1px solid var(--ds-color-warning);
  color: var(--ds-color-secondary);
}

.kg-warning-banner--error {
  background: var(--ds-color-error-bg);
  border: 1px solid var(--ds-color-error);
  color: var(--ds-color-error-text);
}

.kg-warning-banner--info {
  background: var(--ds-color-primary-bg);
  border: 1px solid var(--ds-color-primary);
  color: var(--ds-color-primary-text);
}

.kg-warning-banner--neutral {
  background: var(--ds-color-light);
  border: 1px solid var(--ds-color-border);
  color: var(--ds-color-label);
}
</style>
