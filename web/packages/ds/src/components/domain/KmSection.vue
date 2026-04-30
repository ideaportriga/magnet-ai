<script setup lang="ts">
/**
 * `<km-section>` — settings-style two-column section: title/subtitle on the
 * left, content slot on the right. Drop-in for the legacy.
 */

withDefaults(
  defineProps<{
    title?: string
    subTitle?: string
  }>(),
  {
    title: '',
    subTitle: '',
  },
)
</script>

<template>
  <section class="km-section sidebar" data-test="km-section">
    <header class="km-section__head stack" data-gap="2xs">
      <h3 v-if="title" class="km-section__title">{{ title }}</h3>
      <p v-if="subTitle" class="km-section__sub">{{ subTitle }}</p>
    </header>
    <div class="km-section__body">
      <slot />
    </div>
  </section>
</template>

<style>
.km-section {
  --sidebar-side-width: 18rem;
  --sidebar-content-min: 60%;
  --sidebar-gap: var(--ds-space-lg);
}
.km-section__head { max-inline-size: 18rem; }
.km-section__title {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}
.km-section__sub {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  margin: 0;
}
.km-section__body { padding-inline-start: var(--ds-space-lg); }
</style>
