<template>
  <span class="kg-inline-field" :class="{ 'kg-inline-field--interactive': interactive }">
    <slot />
    <q-tooltip v-if="tooltip" anchor="top middle" self="bottom middle">
      {{ tooltip }}
    </q-tooltip>
  </span>
</template>

<script setup lang="ts">
interface Props {
  interactive?: boolean
  tooltip?: string
}

withDefaults(defineProps<Props>(), {
  interactive: false,
  tooltip: undefined,
})
</script>

<style scoped>
.kg-inline-field {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-width: 320px;
  min-width: 0;
  overflow: hidden;
  border-bottom: 1px dashed var(--q-primary-transparent);
  padding: 0 4px 1px;
  color: var(--q-primary);
  font-weight: 500;
  white-space: nowrap;
  transition: border-color 0.15s ease;
}

.kg-inline-field:hover {
  border-bottom-color: var(--q-primary);
}

.kg-inline-field--interactive {
  cursor: pointer;
  user-select: none;
}

.kg-inline-field :deep(.kg-inline-field__input) {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  border: none;
  outline: none;
  background: transparent;
  font-size: inherit;
  font-weight: 500;
  color: var(--q-primary);
  font-family: var(--km-font-mono);
  padding: 0;
  text-align: center;
}

.kg-inline-field :deep(.kg-inline-field__input::placeholder) {
  color: var(--q-primary-transparent);
  font-style: italic;
}
</style>
