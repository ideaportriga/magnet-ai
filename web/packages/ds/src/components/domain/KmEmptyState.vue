<script setup lang="ts">
/**
 * `<km-empty-state>` — replaces the legacy EmptyState (Stylus + q-icon +
 * km-btn). Same public API.
 */

import KmGlyph from './KmGlyph.vue'
import KmBtn from './KmBtn.vue'

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
      <KmBtn
        class="km-empty-state__action"
        variant="primary"
        :data-test="actionLabel"
        :label="actionLabel"
        @click="$emit('click')"
      />
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
  background: var(--ds-color-gradient);
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

.km-empty-state__action { flex: none; }
</style>
