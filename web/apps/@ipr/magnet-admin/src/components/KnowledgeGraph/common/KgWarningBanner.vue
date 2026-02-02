<template>
  <div class="kg-warning-banner" :class="`kg-warning-banner--${variant}`">
    <q-icon :name="iconName" :color="iconColor" size="26px" />
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
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.4;
}

.kg-warning-banner--warning {
  background: #fffde7;
  border: 1px solid var(--q-warning);
  color: #5d4037;
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
