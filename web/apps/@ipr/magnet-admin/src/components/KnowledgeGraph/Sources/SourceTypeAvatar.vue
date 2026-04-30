<template>
  <km-card
    class="source-type-card"
    :class="{ 'cursor-pointer': !disabled, 'source-type-card--disabled': disabled }"
    flat
    bordered
    clickable
    @click="!disabled && emit('select')"
  >
    <km-badge v-if="comingSoon" tone="warning" :label="m.common_comingSoon()" class="coming-soon-badge text-weight-medium" />
    <div class="km-card-section" style="display: flex; flex-direction: column; align-items: center; justify-content: center">
      <km-avatar :tone="avatarTone" square size="72px" class="border-radius-12">
        <km-image v-if="image" :src="image" width="48px" height="48px" no-spinner no-transition />
        <km-glyph v-else-if="icon" :name="icon" tone="current" size="48px" />
      </km-avatar>
      <div class="text-weight-medium mt-sm">{{ name }}</div>
    </div>
  </km-card>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
import type { KmAvatarTone } from '@ds/components/domain/KmAvatar.vue'

defineProps<{
  name: string
  image?: string
  icon?: string
  avatarTone?: KmAvatarTone
  disabled?: boolean
  comingSoon?: boolean
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()
</script>

<style scoped>
.source-type-card {
  position: relative;
  inline-size: 130px;
  block-size: 130px;
  transition:
    background-color var(--ds-duration-slow) var(--ds-ease-out),
    border-color var(--ds-duration-slow) var(--ds-ease-out),
    box-shadow var(--ds-duration-slow) var(--ds-ease-out),
    transform var(--ds-duration-slow) var(--ds-ease-out);
  border-radius: var(--ds-radius-xl);
  border: 1px solid var(--ds-color-border);
}

.source-type-card:hover:not(.source-type-card--disabled) {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  background-color: var(--ds-color-background);
  border-color: var(--ds-color-border-2);
  transform: translateY(-4px);
}

.source-type-card:active:not(.source-type-card--disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.source-type-card--disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.coming-soon-badge {
  position: absolute;
  inset-block-start: -7px;
  inset-inline-end: 20px;
  font-size: var(--ds-font-size-caption);
  z-index: 1;
}

.border-radius-12 {
  border-radius: var(--ds-radius-xl);
}
</style>
