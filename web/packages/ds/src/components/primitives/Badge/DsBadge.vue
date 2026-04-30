<script setup lang="ts">
/**
 * Badge — pill-shaped status / counter. Replaces shadcn `<Badge>`.
 *
 *   <DsBadge variant="primary">Beta</DsBadge>
 *   <DsBadge variant="destructive">3</DsBadge>
 *   <DsBadge variant="outline">Draft</DsBadge>
 *   <DsBadge display="status" tone="success">Ready</DsBadge>
 *   <DsBadge display="tag" tone="brand" shape="square">RAG</DsBadge>
 */

import { Primitive, type PrimitiveProps } from 'reka-ui'

export type DsBadgeVariant = 'primary' | 'secondary' | 'destructive' | 'outline'
export type DsBadgeTone = 'neutral' | 'neutral-strong' | 'brand' | 'info' | 'context' | 'success' | 'warning' | 'danger' | 'score'
export type DsBadgeDisplay = 'status' | 'tag' | 'filter' | 'input-token' | 'counter' | 'dot'
export type DsBadgeShape = 'pill' | 'square'

withDefaults(
  defineProps<PrimitiveProps & {
    /** Legacy/basic visual variant. Prefer `display` + `tone` for new UI. */
    variant?: DsBadgeVariant
    /** Component role in the UI. */
    display?: DsBadgeDisplay
    /** Semantic meaning, independent from raw color tokens. */
    tone?: DsBadgeTone
    /** Shape is intentionally closed; `square` replaces old ad hoc chip radius. */
    shape?: DsBadgeShape
  }>(),
  {
    as: 'span',
    variant: 'primary',
    shape: 'pill',
  },
)
</script>

<template>
  <Primitive
    class="ds-badge"
    :as="as"
    :as-child="asChild"
    :data-variant="variant"
    :data-display="display"
    :data-tone="tone"
    :data-shape="shape"
    data-test="ds-badge"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-xs);
  inline-size: fit-content;
  white-space: nowrap;
  border: 1px solid transparent;
  border-radius: var(--ds-radius-full);
  padding: 2px var(--ds-space-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-tight);
  overflow: hidden;
  transition:
    background-color var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out);
}

.ds-badge > svg {
  flex: none;
  inline-size: 0.75rem;
  block-size: 0.75rem;
  pointer-events: none;
}

/* ---------- variants ---------- */
.ds-badge[data-variant='primary'] {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
a.ds-badge[data-variant='primary']:hover { background: var(--ds-color-btn-primary-hover-bg); }

.ds-badge[data-variant='secondary'] {
  background: var(--ds-color-secondary-bg);
  color: var(--ds-color-secondary-text);
}
a.ds-badge[data-variant='secondary']:hover { background: var(--ds-color-control-hover-bg); }

.ds-badge[data-variant='destructive'] {
  background: var(--ds-color-error);
  color: var(--ds-color-static-white);
}
a.ds-badge[data-variant='destructive']:hover { background: var(--ds-color-error-text); }

.ds-badge[data-variant='outline'] {
  background: transparent;
  color: var(--ds-color-black);
  border-color: var(--ds-color-border);
}
a.ds-badge[data-variant='outline']:hover {
  background: var(--ds-color-control-hover-bg);
}

/* ---------- target display API ---------- */
.ds-badge[data-tone='neutral'] {
  background: var(--ds-color-secondary-bg);
  color: var(--ds-color-secondary-text);
  border-color: transparent;
}
.ds-badge[data-tone='neutral-strong'] {
  background: var(--ds-color-text-grey);
  color: var(--ds-color-static-white);
  border-color: transparent;
}
.ds-badge[data-tone='brand'] {
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
  border-color: transparent;
}
.ds-badge[data-tone='info'] {
  background: color-mix(in srgb, var(--ds-color-info) 14%, transparent);
  color: var(--ds-color-info);
  border-color: transparent;
}
.ds-badge[data-tone='context'] {
  background: color-mix(in srgb, #8e24aa 14%, transparent);
  color: #8e24aa;
  border-color: transparent;
}
.ds-badge[data-tone='success'] {
  background: var(--ds-color-success-bg, color-mix(in srgb, var(--ds-color-success-text) 14%, transparent));
  color: var(--ds-color-success-text);
  border-color: transparent;
}
.ds-badge[data-tone='warning'] {
  background: var(--ds-color-warning-bg);
  color: var(--ds-color-warning-text);
  border-color: transparent;
}
.ds-badge[data-tone='danger'] {
  background: var(--ds-color-error-bg);
  color: var(--ds-color-error-text);
  border-color: transparent;
}
.ds-badge[data-tone='score'] {
  background: var(--ds-color-score-relevant);
  color: var(--ds-color-score-relevant-text);
  border-color: transparent;
}

.ds-badge[data-variant='outline'][data-tone] {
  background: transparent;
  border-color: currentColor;
}

.ds-badge[data-shape='pill'] { border-radius: var(--ds-radius-full); }
.ds-badge[data-shape='square'] { border-radius: var(--ds-radius-sm); }

.ds-badge[data-display='counter'] {
  min-inline-size: 20px;
  padding-inline: var(--ds-space-xs);
}
.ds-badge[data-display='filter'],
.ds-badge[data-display='input-token'] {
  min-block-size: 24px;
  padding-inline: var(--ds-space-sm);
}
.ds-badge[data-display='dot'] {
  inline-size: 8px;
  block-size: 8px;
  padding: 0;
  border-radius: 50%;
}
</style>
