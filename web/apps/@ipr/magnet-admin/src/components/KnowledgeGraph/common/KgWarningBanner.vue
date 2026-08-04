<template>
  <div class="kg-warning-banner" :class="`kg-warning-banner--${variant}`">
    <q-icon :name="iconName" :color="iconColor" size="22px" class="kg-warning-banner__icon" />
    <div class="col">
      <div v-if="title" class="kg-warning-banner__title">{{ title }}</div>
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
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'warning',
})

const variantConfig: Record<BannerVariant, { icon: string; iconColor: string }> = {
  warning: { icon: 'warning', iconColor: 'orange-9' },
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
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.kg-warning-banner__icon {
  margin-top: 1px;
}

.kg-warning-banner__title {
  font-weight: 600;
  margin-bottom: 2px;
}

.kg-warning-banner--warning {
  background: #fff4e5;
  border: 1px solid #ffb74d;
  color: #663c00;
}

.kg-warning-banner--error {
  background: #ffebee;
  border: 1px solid var(--q-negative);
  color: #b71c1c;
}

.kg-warning-banner--info {
  background: #e3f2fd;
  border: 1px solid var(--q-primary);
  color: #0d47a1;
}

.kg-warning-banner--neutral {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  color: #616161;
}
</style>
