<script setup lang="ts">
/**
 * Avatar — image with graceful fallback to initials/placeholder.
 *
 *   <DsAvatar :src="user.photo" :name="user.fullName" />
 */

import { AvatarFallback, AvatarImage, AvatarRoot } from 'reka-ui'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    src?: string
    /** Used to derive initials when the image fails to load. */
    name?: string
    /** Visual size. */
    size?: 'sm' | 'md' | 'lg' | 'xl'
    /** Alt text — falls back to `name`. */
    alt?: string
  }>(),
  {
    size: 'md',
  },
)

const initials = computed(() => {
  const source = props.name ?? ''
  if (!source) return '?'
  return source
    .split(/\s+/)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .filter(Boolean)
    .slice(0, 2)
    .join('') || '?'
})
</script>

<template>
  <AvatarRoot class="ds-avatar" :data-size="size" data-test="ds-avatar">
    <AvatarImage v-if="src" :src="src" :alt="alt ?? name ?? ''" class="ds-avatar__image" />
    <AvatarFallback class="ds-avatar__fallback">
      {{ initials }}
    </AvatarFallback>
  </AvatarRoot>
</template>

<style>
.ds-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 32px;
  block-size: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--ds-color-primary-light);
  color: var(--ds-color-primary);
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-semibold);
  user-select: none;
}
.ds-avatar[data-size='sm'] { inline-size: 24px; block-size: 24px; font-size: var(--ds-font-size-xs); }
.ds-avatar[data-size='md'] { inline-size: 32px; block-size: 32px; }
.ds-avatar[data-size='lg'] { inline-size: 40px; block-size: 40px; font-size: var(--ds-font-size-label); }
.ds-avatar[data-size='xl'] { inline-size: 64px; block-size: 64px; font-size: var(--ds-font-size-body-lg); }

.ds-avatar__image {
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}
.ds-avatar__fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 100%;
  block-size: 100%;
}
</style>
