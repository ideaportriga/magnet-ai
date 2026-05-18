<script setup lang="ts">
/**
 * `<km-input>` — drop-in for the legacy Input component.
 *
 * Public API preserved (subset that's actually used in admin):
 *   modelValue, type, placeholder, disabled, readonly, autogrow, maxLength,
 *   autofocus, clearable, suffix, prefix, iconBefore, customClearAction,
 *   beforeIconAction, hideBottomSpace, inputClass, rules, errorMessage,
 *   borderless, dense, rounded, height, label, multiline, rows,
 *   minRows, maxRows
 *
 * Validation flows through `useValidation` from `@shared` to keep the same
 * `:rules='[required(), …]'` semantics. New code should use `<DsField>` +
 * `<DsInput>` / `<DsTextarea>` directly.
 *
 * Internally renders a `<DsInput>` or `<DsTextarea>` (cube-CSS primitive)
 * inside a `<DsInputGroup>`-style frame for icon / clear / prefix / suffix
 * affordances.
 */

import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  toRefs,
  useId,
  useSlots,
  useTemplateRef,
  watch,
} from 'vue'
import useValidation from '@shared/composables/useValidation'
import DsInput from '../primitives/Input/DsInput.vue'
import DsTextarea from '../primitives/Textarea/DsTextarea.vue'
import KmGlyph from './KmGlyph.vue'
import KmIcon from './KmIcon.vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string | number | null
    type?: string
    placeholder?: string
    disabled?: boolean
    readonly?: boolean
    autogrow?: boolean
    maxLength?: string | number
    autofocus?: boolean
    clearable?: boolean
    suffix?: string
    prefix?: string
    iconBefore?: string
    customClearAction?: ((event: MouseEvent) => void) | false
    beforeIconAction?: (event: MouseEvent) => void
    hideBottomSpace?: boolean
    inputClass?: string
    rules?: Array<(value: unknown) => boolean | string> | object
    /** Pass-through error message (overrides validation output). */
    errorMessage?: string
    rows?: number | string
    minRows?: number | string
    maxRows?: number | string
    /** Treat as multi-line textarea regardless of `type`. */
    multiline?: boolean
    label?: string
    /** Visual size. */
    dense?: boolean
    /** Borderless / rounded inherit from legacy Quasar look. */
    borderless?: boolean
    rounded?: boolean
    /** Native attributes forwarded to the inner <input>. Required for
     *  password-manager autofill (e.g. autocomplete="current-password"). */
    name?: string
    autocomplete?: string
    inputmode?: 'none' | 'text' | 'tel' | 'url' | 'email' | 'numeric' | 'decimal' | 'search'
  }>(),
  {
    type: 'text',
    rows: 1,
    autofocus: false,
    autogrow: false,
    customClearAction: false,
    beforeIconAction: () => {},
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string | number | null]
  input: [value: string]
  change: [value: Event]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  keydown: [event: KeyboardEvent]
}>()

const { modelValue, rules } = toRefs(props)
const { errorMessage: ruleError, validate, resetValidation } = useValidation(modelValue, rules)

const inputId = useId()

type NativeInputElement = HTMLInputElement | HTMLTextAreaElement
type ExposedInput = NativeInputElement | {
  focus?: (options?: FocusOptions) => void
  blur?: () => void
  el?: HTMLTextAreaElement | { value?: HTMLTextAreaElement | null } | null
}

const inputRef = useTemplateRef<ExposedInput>('input')
const slots = useSlots()
const focused = ref(false)
const textareaIsAtMinRows = ref(true)
let textareaResizeObserver: ResizeObserver | undefined

const finalError = computed<string | undefined>(() => {
  if (props.errorMessage) return props.errorMessage
  return (ruleError.value as string) || undefined
})

const showClear = computed(
  () => props.clearable && props.modelValue !== '' && props.modelValue != null,
)

const isTextarea = computed(
  () => props.multiline || props.autogrow || props.type === 'textarea',
)

const hasAppend = computed(() => Boolean(slots.append))

function toPositiveRowCount(value: number | string | undefined) {
  const rowCount = Number(value)
  if (!Number.isFinite(rowCount) || rowCount <= 0) return undefined
  return Math.floor(rowCount)
}

const minRowCount = computed(() => toPositiveRowCount(props.minRows))
const maxRowCount = computed(() => toPositiveRowCount(props.maxRows))
const isSingleRowTextarea = computed(
  () => isTextarea.value && minRowCount.value === 1 && textareaIsAtMinRows.value,
)

const textareaStyle = computed(() => {
  const style: Record<string, string> = {}
  const minRows = minRowCount.value
  const maxRows = maxRowCount.value

  if (minRows) style['--km-input-textarea-min-content-size'] = `${minRows}lh`
  if (maxRows) style['--km-input-textarea-max-content-size'] = `${minRows ? Math.max(maxRows, minRows) : maxRows}lh`

  return style
})

const iconBeforeSize = computed(() => {
  if (!props.iconBefore || props.iconBefore.startsWith('--theme')) return '18px'
  return /\s/.test(props.iconBefore) ? '16px' : '18px'
})

function onFocus(event: FocusEvent) {
  focused.value = true
  emit('focus', event)
}
function onBlur(event: FocusEvent) {
  focused.value = false
  emit('blur', event)
}
function onInput(event: Event) {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  emit('input', target.value)
  emit('update:modelValue', target.value)
  if (target instanceof HTMLTextAreaElement) resizeTextarea(target)
}
function onChange(event: Event) {
  emit('change', event)
}
function onClear() {
  if (props.customClearAction) {
    props.customClearAction(new MouseEvent('click'))
    return
  }
  emit('update:modelValue', '')
  emit('input', '')
  resetValidation()
  inputRef.value?.focus?.()
}

function resolveTextareaElement() {
  const current = inputRef.value
  if (!current) return undefined
  if (current instanceof HTMLTextAreaElement) return current
  if (current instanceof HTMLInputElement) return undefined

  const exposedEl = current.el
  if (exposedEl instanceof HTMLTextAreaElement) return exposedEl
  if (exposedEl?.value instanceof HTMLTextAreaElement) return exposedEl.value
  return undefined
}

function resizeTextarea(textarea = resolveTextareaElement()) {
  if (!props.autogrow || !isTextarea.value || !textarea) return

  textarea.style.blockSize = 'auto'

  const style = window.getComputedStyle(textarea)
  const minBlockSize = Number.parseFloat(style.minBlockSize) || 0
  const maxBlockSize = Number.parseFloat(style.maxBlockSize)
  const hasMaxBlockSize = Number.isFinite(maxBlockSize) && maxBlockSize > 0
  const scrollBlockSize = textarea.scrollHeight
  const nextBlockSize = Math.max(
    minBlockSize,
    hasMaxBlockSize ? Math.min(scrollBlockSize, maxBlockSize) : scrollBlockSize,
  )

  textarea.style.blockSize = `${nextBlockSize}px`
  textarea.style.overflowY = hasMaxBlockSize && scrollBlockSize > maxBlockSize ? 'auto' : 'hidden'
  textareaIsAtMinRows.value = nextBlockSize <= minBlockSize + 1
}

function queueTextareaResize() {
  if (!props.autogrow || !isTextarea.value) return
  void nextTick(() => resizeTextarea())
}

watch(
  () => [props.modelValue, props.autogrow, props.minRows, props.maxRows, props.rows, isTextarea.value],
  queueTextareaResize,
  { flush: 'post' },
)

onMounted(() => {
  queueTextareaResize()

  const textarea = resolveTextareaElement()
  if (textarea && typeof ResizeObserver !== 'undefined') {
    textareaResizeObserver = new ResizeObserver(queueTextareaResize)
    textareaResizeObserver.observe(textarea.parentElement ?? textarea)
  }
})

onBeforeUnmount(() => {
  textareaResizeObserver?.disconnect()
})

defineExpose({
  validate,
  resetValidation,
  focus: (options?: FocusOptions) => inputRef.value?.focus?.(options),
  blur: () => inputRef.value?.blur?.(),
})
</script>

<template>
  <span
    class="km-input"
    :data-state="finalError ? 'error' : focused ? 'focused' : undefined"
    :data-dense="dense ? 'true' : undefined"
    :data-borderless="borderless ? 'true' : undefined"
    :data-rounded="rounded ? 'true' : undefined"
    :data-disabled="disabled ? 'true' : undefined"
    :data-textarea="isTextarea ? 'true' : undefined"
    :data-append="hasAppend ? 'true' : undefined"
    :data-single-row="isSingleRowTextarea ? 'true' : undefined"
  >
    <label v-if="label" :for="inputId" class="km-input__label">{{ label }}</label>

    <div class="km-input__control">
      <span v-if="iconBefore" class="km-input__prefix" @click="beforeIconAction">
        <KmIcon
          v-if="iconBefore.startsWith('--theme')"
          :name="iconBefore.replace('--theme-', '')"
          width="18"
          height="18"
        />
        <KmGlyph v-else :name="iconBefore" :size="iconBeforeSize" />
      </span>

      <span v-if="prefix" class="km-input__affix">{{ prefix }}</span>

      <DsTextarea
        v-if="isTextarea"
        :id="inputId"
        ref="input"
        :model-value="modelValue ?? ''"
        :placeholder="placeholder"
        :readonly="readonly"
        :disabled="disabled"
        :autofocus="autofocus"
        :maxlength="maxLength || undefined"
        :rows="rows"
        :style="textareaStyle"
        :aria-invalid="finalError ? true : undefined"
        :name="name"
        :autocomplete="autocomplete"
        class="km-input__field"
        :class="[inputClass, { 'km-input__field--autogrow': autogrow }]"
        data-test="km-input"
        @input="onInput"
        @change="onChange"
        @focus="onFocus"
        @blur="onBlur"
        @keydown="emit('keydown', $event)"
      />

      <DsInput
        v-else
        :id="inputId"
        ref="input"
        :type="type"
        :model-value="modelValue ?? ''"
        :placeholder="placeholder"
        :readonly="readonly"
        :disabled="disabled"
        :autofocus="autofocus"
        :maxlength="maxLength || undefined"
        :aria-invalid="finalError ? true : undefined"
        :size="dense ? 'sm' : 'md'"
        :name="name"
        :autocomplete="autocomplete"
        :inputmode="inputmode"
        class="km-input__field"
        :class="inputClass"
        data-test="km-input"
        @input="onInput"
        @change="onChange"
        @focus="onFocus"
        @blur="onBlur"
        @keydown="emit('keydown', $event)"
      />

      <span v-if="suffix" class="km-input__affix">{{ suffix }}</span>

      <span v-if="hasAppend" class="km-input__append">
        <slot name="append" :height="0" />
      </span>

      <button
        v-if="showClear || customClearAction"
        type="button"
        class="km-input__clear"
        aria-label="Clear"
        data-test="km-input-clear"
        @click="onClear"
      >
        <KmGlyph name="close" size="20px" />
      </button>
    </div>

    <slot name="menu" />

    <p v-if="finalError && !hideBottomSpace" class="km-input__error">{{ finalError }}</p>
  </span>
</template>

<style>
.km-input {
  /* Block-level flex container — `<span>` element keeps the inline-level
   * tag for backwards-compat (CSS resets in app code may target span
   * children of `.km-input`), but the visual box is block so block-level
   * siblings beneath the input drop onto the next line cleanly.
   *
   * `block-size: auto !important` cancels the legacy Quasar-era theme rule
   * `.km-input { height: var(--field-height) !important }` that was wired
   * for the old `<q-input>` wrapper — the new wrapper is NOT a single-row
   * field, its size is driven by the inner `<DsInput>` / `<DsTextarea>`. */
  display: flex !important;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  inline-size: 100%;
  block-size: auto !important;
}

.km-input__label {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-label);
  font-weight: var(--ds-font-weight-medium);
}

/* The control row is a flex container that stitches a leading icon, prefix
 * affix, the actual `<DsInput>` / `<DsTextarea>`, suffix affix, append slot
 * and clear button into a single rounded chrome. The wrapper itself owns
 * the border / background / focus-ring; the inner `<DsInput>` is stripped
 * of its own chrome so a leading icon visually sits *inside* the field. */
.km-input__control {
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
  inline-size: 100%;
  min-inline-size: 0;
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  padding-inline: var(--ds-space-sm);
  block-size: 36px;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.km-input[data-dense='true'] .km-input__control {
  block-size: 32px;
}
.km-input[data-textarea='true'] .km-input__control {
  align-items: stretch;
  block-size: auto;
  padding-block: var(--ds-space-2xs);
}
.km-input[data-append='true'] .km-input__control {
  padding-inline-end: var(--ds-space-2xs);
}
.km-input__control:hover {
  border-color: var(--ds-color-control-hover-border);
}
.km-input__control:focus-within {
  border-color: var(--ds-color-primary);
  box-shadow: inset 0 0 0 2px var(--ds-color-primary-transparent);
}
.km-input[data-state='error'] .km-input__control {
  border-color: var(--ds-color-error);
}
.km-input[data-state='error'] .km-input__control:focus-within {
  box-shadow: inset 0 0 0 2px var(--ds-color-error-bg);
}
.km-input[data-disabled='true'] .km-input__control {
  opacity: 0.5;
  cursor: not-allowed;
}
.km-input[data-borderless='true'] .km-input__control {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
}
.km-input[data-rounded='true'] .km-input__control {
  border-radius: var(--ds-radius-full);
}

/* Strip the inner `<DsInput>` / `<DsTextarea>` chrome — the wrapper above
 * is the visual envelope. The inner input keeps its native focus ring off
 * since `.km-input__control:focus-within` provides the focus indicator. */
.km-input .km-input__field {
  flex: 1 1 auto;
  min-inline-size: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
  padding-inline: 0;
  block-size: auto;
  box-shadow: none;
}
.km-input .km-input__field:hover,
.km-input .km-input__field:focus-visible,
.km-input .km-input__field[aria-invalid='true'] {
  border: 0;
  box-shadow: none;
}

/* Legacy contract: when a `rows` attribute is given, the textarea must
 * size itself by row-count, not by content. `<DsTextarea>` ships with
 * `field-sizing: content` (per shadcn defaults) which would override `rows`
 * — opt out for non-autogrow `<KmInput type="textarea">` usages. The
 * `field-sizing` keyword for "honour rows" is `fixed`, not `auto`. */
.km-input[data-textarea='true'] .km-input__field {
  field-sizing: fixed;
  --km-input-textarea-block-padding: calc(var(--ds-space-2xs) * 2);
  min-block-size: calc(var(--km-input-textarea-min-content-size, 4lh) + var(--km-input-textarea-block-padding));
  padding-block: var(--ds-space-2xs);
  line-height: var(--ds-line-height-relaxed);
}

.km-input__field--autogrow {
  resize: none;
  field-sizing: content;
  max-block-size: calc(var(--km-input-textarea-max-content-size, 999lh) + var(--km-input-textarea-block-padding));
  overflow-block: auto;
}

.km-input__prefix,
.km-input__clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  background: transparent;
  border: 0;
  padding: 0;
  color: var(--ds-color-icon);
  cursor: pointer;
}
.km-input__prefix {
  inline-size: 18px;
  block-size: 18px;
}
.km-input__prefix .km-glyph,
.km-input__prefix .km-icon {
  max-inline-size: 100%;
  max-block-size: 100%;
}
.km-input__clear:hover { color: var(--ds-color-secondary); }

.km-input__append {
  display: inline-flex;
  align-self: stretch;
  align-items: center;
  justify-content: center;
  flex: none;
}

.km-input[data-textarea='true'] .km-input__append {
  align-items: flex-end;
}

.km-input[data-textarea='true'][data-single-row='true'] .km-input__append {
  align-items: center;
}

.km-input__affix {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
}

.km-input__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  margin: 0;
}

</style>
