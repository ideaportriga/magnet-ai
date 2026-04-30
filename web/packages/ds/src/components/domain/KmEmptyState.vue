<script setup lang="ts">
/**
 * `<km-empty-state>` — replaces the legacy EmptyState (Stylus + q-icon +
 * km-btn). Same public API.
 */

import KmGlyph from './KmGlyph.vue'

withDefaults(
  defineProps<{
    icon?: string
    label?: string
    description?: string
    actionLabel?: string
  }>(),
  {
    icon: 'magic',
    label: 'This AI App has no AI Tabs yet',
    description: 'Add AI Tabs to connect your AI tools.',
    actionLabel: 'New AI Tab',
  },
)

defineEmits<{
  click: []
}>()
</script>

<template>
  <div class="km-empty-state stack" data-gap="md" data-test="km-empty-state">
    <div class="cluster" data-justify="center">
      <KmGlyph :name="icon" size="2rem" class="km-empty-state__icon" />
    </div>
    <h3 class="km-empty-state__title">{{ label }}</h3>
    <p class="km-empty-state__description">{{ description }}</p>
    <div v-if="actionLabel" class="cluster" data-justify="center">
      <button
        class="km-empty-state__action"
        type="button"
        :data-test="actionLabel"
        @click="$emit('click')"
      >
        {{ actionLabel }}
      </button>
    </div>
  </div>
</template>

<style>
.km-empty-state {
  max-inline-size: 400px;
  padding: var(--ds-space-lg) var(--ds-space-3xl);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-xl);
  background: var(--ds-color-light-grey);
  text-align: center;
}

.km-empty-state__icon {
  background: linear-gradient(121.5deg, var(--ds-color-primary) 9.69%, #e30052 101.29%);
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}

.km-empty-state__title {
  font-size: var(--ds-font-size-body-lg);
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}

.km-empty-state__description {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
  margin: 0;
}

.km-empty-state__action {
  padding: var(--ds-space-xs) var(--ds-space-md);
  background: var(--ds-color-btn-primary-bg);
  color: var(--ds-color-btn-primary-text);
  border: 0;
  border-radius: var(--ds-radius-md);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  cursor: pointer;
}
.km-empty-state__action:hover { background: var(--ds-color-btn-primary-hover-bg); }
</style>
