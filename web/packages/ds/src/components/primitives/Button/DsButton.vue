<script setup lang="ts">
/**
 * Button — reka-ui Primitive wrapper. Mirrors the shadcn-vue button API
 * (variant + size) but styled with cube CSS tokens (`--ds-*`) instead of
 * Tailwind utilities.
 *
 *   <DsButton variant="primary" size="md">Save</DsButton>
 *   <DsButton variant="ghost" size="icon"><Icon /></DsButton>
 *   <DsButton as-child><RouterLink to="/x">Open</RouterLink></DsButton>
 */

import { Primitive, type PrimitiveProps } from 'reka-ui'

export type DsButtonVariant =
  | 'primary'
  | 'destructive'
  | 'outline'
  | 'secondary'
  | 'ghost'
  | 'link'

export type DsButtonSize = 'md' | 'sm' | 'lg' | 'icon' | 'icon-xs' | 'icon-sm' | 'icon-lg'

export type DsButtonJustify = 'start' | 'center' | 'end' | 'between'

withDefaults(
  defineProps<
    PrimitiveProps & {
      variant?: DsButtonVariant
      size?: DsButtonSize
      /** CUBE modifier — content alignment along the inline axis. */
      justify?: DsButtonJustify
      /** CUBE modifier — fill container inline-size. */
      block?: boolean
    }
  >(),
  {
    as: 'button',
    variant: 'primary',
    size: 'md',
  },
)
</script>

<template>
  <Primitive
    class="ds-button"
    :as="as"
    :as-child="asChild"
    :data-variant="variant"
    :data-size="size"
    :data-justify="justify"
    :data-block="block ? '' : undefined"
    data-test="ds-button"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-button {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  flex: none;
  white-space: nowrap;
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-none);
  cursor: pointer;
  user-select: none;
  text-decoration: none;
  transition:
    background-color var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}

.ds-button:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

.ds-button:disabled,
.ds-button[aria-disabled='true'] {
  opacity: 0.5;
  pointer-events: none;
  cursor: not-allowed;
}

.ds-button > svg {
  flex: none;
  inline-size: 1em;
  block-size: 1em;
  pointer-events: none;
}

/* ---------- variants ---------- */
.ds-button[data-variant='primary'] {
  background: var(--ds-color-btn-primary-bg);
  color: var(--ds-color-btn-primary-text);
}
.ds-button[data-variant='primary']:hover { background: var(--ds-color-btn-primary-hover-bg); }
.ds-button[data-variant='primary']:active { background: var(--ds-color-btn-primary-active-bg); }

.ds-button[data-variant='destructive'] {
  background: var(--ds-color-error);
  color: var(--ds-color-static-white);
}
.ds-button[data-variant='destructive']:hover { background: var(--ds-color-error-text); }

.ds-button[data-variant='outline'] {
  background: transparent;
  color: var(--ds-color-black);
  border-color: var(--ds-color-border);
}
.ds-button[data-variant='outline']:hover {
  background: var(--ds-color-control-hover-bg);
  border-color: var(--ds-color-control-hover-border);
}

.ds-button[data-variant='secondary'] {
  background: var(--ds-color-secondary-bg);
  color: var(--ds-color-secondary-text);
}
.ds-button[data-variant='secondary']:hover {
  background: var(--ds-color-control-hover-bg);
}

.ds-button[data-variant='ghost'] {
  background: var(--ds-color-btn-flat-bg);
  color: var(--ds-color-btn-flat-text);
}
.ds-button[data-variant='ghost']:hover {
  background: var(--ds-color-btn-flat-hover-bg);
  color: var(--ds-color-btn-flat-hover-text);
}
.ds-button[data-variant='ghost']:active {
  background: var(--ds-color-btn-flat-active-bg);
}

.ds-button[data-variant='link'] {
  background: transparent;
  color: var(--ds-color-primary);
  border-color: transparent;
  padding: 0;
  block-size: auto;
  text-underline-offset: 4px;
}
.ds-button[data-variant='link']:hover { text-decoration: underline; }

/* ---------- sizes ---------- */
.ds-button[data-size='md'] {
  block-size: 36px;
  padding-inline: var(--ds-space-lg);
}
.ds-button[data-size='sm'] {
  block-size: 32px;
  padding-inline: var(--ds-space-md);
  gap: var(--ds-space-xs);
}
.ds-button[data-size='lg'] {
  block-size: 40px;
  padding-inline: var(--ds-space-2xl);
}
.ds-button[data-size='icon'] {
  inline-size: 36px;
  block-size: 36px;
  padding-inline: 0;
}
.ds-button[data-size='icon-xs'] {
  inline-size: 26px;
  block-size: 26px;
  padding-inline: 0;
}
.ds-button[data-size='icon-sm'] {
  inline-size: 32px;
  block-size: 32px;
  padding-inline: 0;
}
.ds-button[data-size='icon-lg'] {
  inline-size: 40px;
  block-size: 40px;
  padding-inline: 0;
}

/* link variant ignores size padding/height */
.ds-button[data-variant='link'][data-size] {
  block-size: auto;
  inline-size: auto;
  padding-inline: 0;
}

/* ---------- justify modifier (CUBE) ----------
 * Default is center (when no `data-justify` is set). Explicit modifiers
 * override that default without specificity battles. */
.ds-button:not([data-justify])     { justify-content: center; }
.ds-button[data-justify='start']   { justify-content: flex-start; text-align: start; }
.ds-button[data-justify='center']  { justify-content: center;     text-align: center; }
.ds-button[data-justify='end']     { justify-content: flex-end;   text-align: end; }
.ds-button[data-justify='between'] { justify-content: space-between; }

/* ---------- block modifier — fills container inline-size (CUBE) ---------- */
.ds-button[data-block] { inline-size: 100%; }
</style>
