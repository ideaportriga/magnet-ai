<script setup lang="ts">
/**
 * `<km-icon-picker>` — modal grid picker for FontAwesome v5 icon names.
 * Icon list is vendored as `fa-v5-icons.json` from legacy FontAwesome v5
 * metadata. Replace with Iconify in the icon-system migration.
 *
 * Emits:
 *   - `update:modelValue` — selected icon class string (e.g. `fas fa-folder`)
 *   - `update:modal` — close request
 */

import { computed, ref } from 'vue'
import iconList from './fa-v5-icons.json'
import kebabCase from 'lodash/kebabCase'
import DsDialog from '../primitives/Dialog/DsDialog.vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmInput from './KmInput.vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    modal?: boolean
    searchPlaceholder?: string
  }>(),
  {
    modal: false,
    searchPlaceholder: 'Search icons',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:modal': [value: boolean]
}>()

const PAGE_SIZE = 36
const search = ref('')
const page = ref(1)

interface IconEntry {
  name: string
  title: string
}

const icons = computed<IconEntry[]>(() =>
  ((iconList as string[]) ?? []).map((name) => {
    const kebab = kebabCase(name)
    const parts = kebab.split('-')
    return {
      name: `${parts[0]} fa-${parts.slice(1).join('-')}`,
      title: parts.slice(1).join(' '),
    }
  }),
)

const displayIcons = computed(() => {
  if (!search.value) return icons.value
  const needle = search.value.toLowerCase().replace(/\s/g, '')
  return icons.value.filter((icon) => icon.name.toLowerCase().replace(/\s/g, '').includes(needle))
})

const pagination = computed(() => ({
  start: PAGE_SIZE * (page.value - 1),
  end: PAGE_SIZE * page.value,
  maxPages: Math.max(1, Math.ceil(displayIcons.value.length / PAGE_SIZE)),
  count: displayIcons.value.length,
}))

const pageIcons = computed(() => displayIcons.value.slice(pagination.value.start, pagination.value.end))

function handleSearchInput(value: string) {
  page.value = 1
  search.value = value
}

function setIcon(icon: IconEntry) {
  emit('update:modelValue', icon.name)
  emit('update:modal', false)
}
</script>

<template>
  <DsDialog
    :open="modal"
    size="lg"
    data-test="km-icon-picker"
    @update:open="(v) => emit('update:modal', v)"
  >
    <template #title>Select an icon</template>

    <div class="km-icon-picker stack" data-gap="md">
      <KmInput
        :model-value="search"
        :placeholder="searchPlaceholder"
        icon-before="search"
        autofocus
        clearable
        @update:model-value="(v) => handleSearchInput(String(v ?? ''))"
      />

      <div class="km-icon-picker__grid">
        <button
          v-for="icon in pageIcons"
          :key="icon.name"
          type="button"
          class="km-icon-picker__cell"
          :class="{ 'km-icon-picker__cell--active': icon.name === modelValue }"
          @click="setIcon(icon)"
        >
          <KmGlyph :name="icon.name" size="26px" tone="muted" />
          <span class="km-icon-picker__title">{{ icon.title }}</span>
        </button>
      </div>
    </div>

    <template #footer>
      <KmBtn
        flat
        icon="chevron-left"
        :disable="page <= 1"
        @click="page -= 1"
      />
      <span class="km-icon-picker__pagination">
        {{ page }} of {{ pagination.maxPages }}
      </span>
      <KmBtn
        flat
        icon="chevron-right"
        :disable="page >= pagination.maxPages"
        @click="page += 1"
      />
    </template>
  </DsDialog>
</template>

<style>
.km-icon-picker__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--ds-space-sm);
}
.km-icon-picker__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-xs);
  inline-size: 100%;
  block-size: 80px;
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-sm);
  padding: var(--ds-space-md);
  cursor: pointer;
  transition: border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.km-icon-picker__cell:hover { border-color: var(--ds-color-primary); }
.km-icon-picker__cell--active {
  border-color: var(--ds-color-primary);
  background: var(--ds-color-primary-bg);
}
.km-icon-picker__title {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-text-grey);
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  inline-size: 100%;
}

.km-icon-picker__pagination {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  padding: 0 var(--ds-space-sm);
}
</style>
