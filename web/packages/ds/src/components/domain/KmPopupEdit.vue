<script setup lang="ts">
/**
 * `<km-popup-edit>` — small popover that opens on parent click and exposes
 * a save / cancel pair. Replaces Quasar's `<q-popup-edit>`. The slot
 * receives `{ value, set, cancel, save }` so call sites stay declarative.
 */
import { ref, watch, onMounted, onBeforeUnmount, useTemplateRef } from 'vue'
import { PopoverAnchor, PopoverContent, PopoverPortal, PopoverRoot } from 'reka-ui'

const props = defineProps<{
  modelValue?: unknown
  title?: string
  validate?: (value: unknown) => boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
  save: [value: unknown]
  cancel: []
}>()

const open = ref(false)
const draft = ref<unknown>(props.modelValue)

watch(
  () => props.modelValue,
  (v) => { if (!open.value) draft.value = v },
)

function set(v: unknown) { draft.value = v }
function cancel() {
  draft.value = props.modelValue
  open.value = false
  emit('cancel')
}
function save() {
  if (props.validate && !props.validate(draft.value)) return
  emit('update:modelValue', draft.value)
  emit('save', draft.value)
  open.value = false
}

const anchorRef = useTemplateRef<HTMLElement>('anchor')
let parent: HTMLElement | null = null
function onParentClick() { open.value = true }

onMounted(() => {
  parent = (anchorRef.value?.previousElementSibling as HTMLElement) ?? (anchorRef.value?.parentElement as HTMLElement)
  parent?.addEventListener('click', onParentClick)
})
onBeforeUnmount(() => parent?.removeEventListener('click', onParentClick))
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverAnchor as-child>
      <span ref="anchor" class="km-popup-edit__anchor" aria-hidden="true" />
    </PopoverAnchor>
    <PopoverPortal>
      <PopoverContent class="km-popup-edit" side="bottom" align="start" :side-offset="4">
        <header v-if="title" class="km-popup-edit__title">{{ title }}</header>
        <div class="km-popup-edit__body">
          <slot :value="draft" :set="set" :cancel="cancel" :save="save" />
        </div>
        <footer class="km-popup-edit__footer">
          <button type="button" class="km-popup-edit__btn" @click="cancel">Cancel</button>
          <button type="button" class="km-popup-edit__btn km-popup-edit__btn--primary" @click="save">Save</button>
        </footer>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
.km-popup-edit__anchor { display: contents; }
.km-popup-edit {
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md, 8px);
  box-shadow: var(--ds-shadow-lg);
  padding: var(--ds-space-md, 12px);
  min-inline-size: 240px;
  z-index: var(--ds-z-overlay, 2000);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm, 8px);
}
.km-popup-edit__title {
  font-weight: var(--ds-font-weight-medium, 500);
  font-size: var(--ds-font-size-label);
}
.km-popup-edit__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--ds-space-xs, 4px);
}
.km-popup-edit__btn {
  padding: var(--ds-space-xs, 4px) var(--ds-space-md, 12px);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-sm, 6px);
  background: var(--ds-color-white);
  cursor: pointer;
  font: inherit;
}
.km-popup-edit__btn--primary {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
  border-color: var(--ds-color-primary);
}
</style>
