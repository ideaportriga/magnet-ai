<template lang="pug">
.overflow-auto(data-test='pricing-options-table')
  .price-table(
    :data-columns='table.columns.length',
    :data-selectable='selectable ? "true" : undefined',
    :role='selectable ? "radiogroup" : undefined',
    :aria-label='selectable ? "Pricing" : undefined'
  )
    .price-table__row.price-table__head(aria-hidden='true')
      span(v-if='selectable')
      span.price-table__unit {{ table.unit ? `USD per ${table.unit}` : '' }}
      span.price-table__col.column(v-for='column in table.columns', :key='column.kind')
        span {{ LABELS[column.kind] }}
        span.price-table__unit(v-if='column.unit && !table.unit') per {{ column.unit }}

    template(v-for='group in table.groups', :key='String(group.source)')
      .price-table__source.row.items-center.no-wrap.q-gap-8(v-if='showSources', data-test='pricing-source-group')
        q-avatar.price-table__avatar(v-if='sourceHeader(group.source).monogram', size='20px', square) {{ sourceHeader(group.source).monogram }}
        q-avatar.price-table__avatar(v-else, size='20px', square, icon='o_content_paste')
        span.price-table__site {{ sourceHeader(group.source).site }}
        span.price-table__title(v-if='sourceHeader(group.source).title') {{ sourceHeader(group.source).title }}

      component.price-table__row.price-table__option(
        v-for='row in group.rows',
        :key='row.index',
        :is='selectable ? "label" : "div"',
        :data-selected='selectable && row.index === modelValue ? "true" : undefined',
        :data-disabled='selectable && disabled ? "true" : undefined',
        data-test='pricing-option'
      )
        input.price-table__radio(
          v-if='selectable',
          type='radio',
          :name='uid',
          :value='row.index',
          :checked='row.index === modelValue',
          :disabled='disabled',
          :aria-labelledby='`${uid}-${row.index}`',
          @change='emit("update:modelValue", row.index)'
        )
        span.price-table__label(:id='`${uid}-${row.index}`') {{ row.label }}
        span.price-table__price(v-for='column in table.columns', :key='column.kind')
          template(v-if='row.cells[column.kind]')
            | {{ row.cells[column.kind]?.amount }}
            span.price-table__unit(v-if='!column.unit') &nbsp;/ {{ row.cells[column.kind]?.unit }}
          span.price-table__none(v-else) —

        template(v-if='row.longContext')
          span(v-if='selectable')
          span.price-table__long Above {{ row.longContext.threshold }} tokens
          span.price-table__price.price-table__price--long(v-for='column in table.columns', :key='column.kind')
            template(v-if='row.longContext.cells[column.kind]')
              | {{ row.longContext.cells[column.kind]?.amount }}
              span.price-table__unit(v-if='!column.unit') &nbsp;/ {{ row.longContext.cells[column.kind]?.unit }}
            span.price-table__none(v-else) —
</template>

<script setup lang="ts">
/**
 * The pricing options the pasted texts gave for one model (#466), as a
 * comparison table: one row per option, one column per price. The unit is
 * stated once in the corner when all prices share it, else per column / cell.
 * With more than one option the rows are a native radio group — the whole
 * row picks it, arrow keys move between rows.
 *
 * Long-context prices sit under their option in the same columns: picking the
 * option applies them too. Options read from different pasted pages are
 * grouped under the page they came from; indices stay global.
 */
import { computed, useId } from 'vue'

import { pricingTable, type ExtractedPricingOption, type PriceLineKind } from './modelTextFill'
import { siteMonogram, type SourceBlock } from './sourceBlocks'

const props = defineProps<{
  options: ExtractedPricingOption[]
  /** The pasted pages; an option's `source` N is `sources[N - 1]`. */
  sources?: SourceBlock[]
  modelValue: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', index: number): void
}>()

const uid = useId()

const LABELS: Record<PriceLineKind, string> = {
  input: 'Input',
  cached: 'Cached input',
  cacheWrite: 'Cache write',
  cacheWrite1h: '1-hour cache write',
  output: 'Output',
}

const table = computed(() => pricingTable(props.options))
const selectable = computed(() => props.options.length > 1)
const showSources = computed(() => table.value.groups.length > 1)

/** Header of a group of options: the page they were read from. */
function sourceHeader(source: number | null) {
  if (source === null) return { site: 'Other', title: null, monogram: '' }
  const block = props.sources?.[source - 1]
  return {
    site: block?.site ?? `Source ${source}`,
    title: block?.title ?? null,
    monogram: siteMonogram(block?.site),
  }
}
</script>

<style scoped>
/* Lead columns (radio, option name) then one per price; `data-columns` sets the count. */
.price-table {
  --price-lead: minmax(8rem, 1fr);
  --price-columns: 1;
  display: grid;
  grid-template-columns: var(--price-lead) repeat(var(--price-columns), minmax(5rem, max-content));
  gap: 4px 24px;
  min-inline-size: max-content;
  inline-size: 100%;
}
.price-table[data-selectable='true'] {
  --price-lead: max-content minmax(8rem, 1fr);
}
.price-table[data-columns='2'] {
  --price-columns: 2;
}
.price-table[data-columns='3'] {
  --price-columns: 3;
}
.price-table[data-columns='4'] {
  --price-columns: 4;
}
.price-table[data-columns='5'] {
  --price-columns: 5;
}

/* Every row shares the table's columns, so prices line up across options. */
.price-table__row {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: subgrid;
  row-gap: 4px;
  align-items: baseline;
  padding: 6px 8px;
  border-radius: 6px;
}
.price-table__head {
  padding-block: 0;
  font-size: 12px;
  color: var(--q-secondary-text);
  align-items: end;
}
.price-table__col {
  text-align: end;
  font-weight: 600;
}
.price-table__col .price-table__unit {
  font-weight: 400;
}

.price-table__option {
  border: 1px solid transparent;
  transition:
    background-color 0.15s ease-out,
    border-color 0.15s ease-out;
}
label.price-table__option {
  cursor: pointer;
}
label.price-table__option:hover {
  background-color: var(--q-background);
}
.price-table__option[data-selected='true'],
label.price-table__option[data-selected='true']:hover {
  background-color: var(--q-primary-bg);
  border-color: var(--q-primary);
}
.price-table__option[data-disabled='true'] {
  cursor: not-allowed;
}
label.price-table__option[data-disabled='true']:hover {
  background-color: transparent;
}
.price-table__option[data-disabled='true'][data-selected='true'] {
  background-color: transparent;
  border-color: var(--q-border);
}

.price-table__label {
  font-weight: 600;
  overflow-wrap: anywhere;
}
.price-table__price {
  text-align: end;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
.price-table__long,
.price-table__price--long {
  font-size: 12px;
  font-weight: 400;
  color: var(--q-secondary-text);
}
.price-table__unit,
.price-table__none {
  font-size: 12px;
  font-weight: 400;
  color: var(--q-secondary-text);
}

.price-table__radio {
  align-self: center;
  margin: 0;
  accent-color: var(--q-primary);
  cursor: inherit;
}

.price-table__avatar {
  font-size: 12px;
  color: var(--q-primary);
  background: var(--q-primary-bg);
  border-radius: 4px;
}

/* A long page title ellipsizes instead of widening the table. */
.price-table__source {
  grid-column: 1 / -1;
  min-inline-size: 0;
  contain: inline-size;
  padding-block-start: 8px;
  padding-inline: 8px;
  font-size: 13px;
}
.price-table__site {
  flex: none;
  font-weight: 600;
}
.price-table__title {
  min-inline-size: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: var(--q-secondary-text);
}
</style>
