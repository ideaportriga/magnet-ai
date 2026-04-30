<script setup lang="ts">
/**
 * `<km-tree>` — minimal tree view. Each node is `{ label, children?, … }`.
 * Replaces light usage of Quasar's `<q-tree>`. For complex selection /
 * filtering use a dedicated tree library.
 */
import { ref } from 'vue'

export interface KmTreeNode {
  label: string
  key?: string | number
  icon?: string
  children?: KmTreeNode[]
}

const props = defineProps<{
  nodes?: KmTreeNode[]
  /** Default open keys — uncontrolled. */
  defaultExpanded?: Array<string | number>
}>()

const expanded = ref<Set<string | number>>(new Set(props.defaultExpanded ?? []))

function toggle(key: string | number) {
  if (expanded.value.has(key)) expanded.value.delete(key)
  else expanded.value.add(key)
  expanded.value = new Set(expanded.value)
}
function keyOf(n: KmTreeNode, fallback: string): string | number {
  return n.key ?? fallback
}
</script>

<template>
  <ul class="km-tree" role="tree" data-test="km-tree">
    <li
      v-for="(node, idx) in nodes ?? []"
      :key="keyOf(node, String(idx))"
      class="km-tree__node"
      role="treeitem"
      :aria-expanded="node.children?.length ? (expanded.has(keyOf(node, String(idx))) ? 'true' : 'false') : undefined"
    >
      <button
        v-if="node.children?.length"
        type="button"
        class="km-tree__toggle"
        @click="toggle(keyOf(node, String(idx)))"
      >
        <span class="km-tree__chevron" :data-open="expanded.has(keyOf(node, String(idx))) ? 'true' : undefined">▸</span>
        <span v-if="node.icon" class="km-tree__icon"><i :class="node.icon" /></span>
        <span class="km-tree__label">{{ node.label }}</span>
      </button>
      <span v-else class="km-tree__leaf">
        <span v-if="node.icon" class="km-tree__icon"><i :class="node.icon" /></span>
        <span class="km-tree__label">{{ node.label }}</span>
      </span>
      <KmTree
        v-if="node.children?.length && expanded.has(keyOf(node, String(idx)))"
        :nodes="node.children"
        :default-expanded="defaultExpanded"
        class="km-tree__children"
      />
    </li>
  </ul>
</template>

<style>
.km-tree { list-style: ""; margin: 0; padding: 0; }
.km-tree__node { padding-inline-start: var(--ds-space-md, 12px); }
.km-tree__toggle, .km-tree__leaf {
  display: flex;
  gap: var(--ds-space-xs, 4px);
  align-items: center;
  padding: var(--ds-space-2xs, 2px) var(--ds-space-xs, 4px);
  background: transparent;
  border: 0;
  cursor: pointer;
  color: inherit;
  font: inherit;
  text-align: start;
  inline-size: 100%;
}
.km-tree__leaf { cursor: default; }
.km-tree__chevron {
  display: inline-flex;
  inline-size: 12px;
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
}
.km-tree__chevron[data-open='true'] { transform: rotate(90deg); }
.km-tree__children { margin-block-start: var(--ds-space-2xs, 2px); }
</style>
