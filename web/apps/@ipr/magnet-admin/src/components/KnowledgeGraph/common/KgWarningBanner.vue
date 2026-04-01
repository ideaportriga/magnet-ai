<template>
  <div class="kg-warning-banner" :class="`kg-warning-banner--${variant}`">
    <q-icon :name="iconName" :color="iconColor" size="28px" class="q-mr-sm" />
    <div class="col">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type BannerVariant = 'warning' | 'error' | 'info' | 'neutral'

interface Props {
  variant?: BannerVariant
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'warning',
})

const variantConfig: Record<BannerVariant, { icon: string; iconColor: string }> = {
  warning: { icon: 'warning', iconColor: 'yellow-8' },
  error: { icon: 'error', iconColor: 'negative' },
  info: { icon: 'info', iconColor: 'primary' },
  neutral: { icon: 'info', iconColor: 'grey-7' },
}

const iconName = computed(() => props.icon || variantConfig[props.variant].icon)
const iconColor = computed(() => variantConfig[props.variant].iconColor)
</script>

<style scoped>
.kg-warning-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-radius: var(--radius-sm);
  font-size: var(--km-font-size-label);
  line-height: 1.4;
}

.kg-warning-banner--warning {
  background: var(--q-warning-bg);
  border: 1px solid var(--q-warning);
  color: var(--q-secondary);
}

.kg-warning-banner--error {
  background: var(--q-error-bg);
  border: 1px solid var(--q-error);
  color: var(--q-error-text);
}

.kg-warning-banner--info {
  background: var(--q-primary-bg);
  border: 1px solid var(--q-primary);
  color: var(--q-primary-text);
}

.kg-warning-banner--neutral {
  background: var(--q-light);
  border: 1px solid var(--q-border);
  color: var(--q-label);
}
</style>
