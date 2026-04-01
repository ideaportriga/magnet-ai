<template lang="pug">
.row.no-wrap.overflow-hidden.full-height.details-layout
  .col.no-wrap.full-height.justify-center.fit.q-px-md.no-wrap.q-pt-sm.q-pb-lg(:style='contentContainerStyle')
    .column.full-height.no-wrap
      slot(name='breadcrumbs')
        div
      .full-width.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16(v-if='!noHeader')
        .row.items-center.no-wrap.full-width
          .col
            slot(name='header')
              layouts-details-header(
                :name='name',
                @update:name='(value) => $emit("update:name", value)',
                :description='description',
                @update:description='(value) => $emit("update:description", value)',
                :systemName='systemName',
                @update:systemName='(value) => $emit("update:systemName", value)',
                :infoText='infoText'
              )
          .col-auto.row.items-start.no-wrap.q-gap-8.q-ml-md(v-if='$slots["header-actions"]')
            slot(name='header-actions')
        slot(name='subheader', v-if='$slots.subheader || variants?.length > 0')
          layouts-details-sub-header(
            :variants='variants',
            :selectedVariant='selectedVariant',
            :activeVariant='activeVariant',
            @activateVariant='emit("activateVariant")',
            @addVariant='emit("addVariant")',
            @deleteVariant='emit("deleteVariant")',
            @selectVariant='emit("selectVariant", $event)',
            @updateVariantProperty='emit("updateVariantProperty", $event)'
          )
      .col.overflow-hidden.no-wrap.column(:class='noContentWrapper ? "" : "ba-border bg-white border-radius-8 q-pa-16"', style='min-height: 0')
        slot(name='content')
          div Content
  .col-auto
    slot(name='drawer')
</template>

<script setup>
/* eslint-disable */
const props = defineProps({
  name: {
    type: String,
  },
  description: {
    type: String,
  },
  systemName: {
    type: String,
  },
  infoText: {
    type: String,
    default: 'It is highly recommended to fill in system name only once and not change it later.',
  },
  noHeader: {
    type: Boolean,
    default: false,
  },
  noContentWrapper: {
    type: Boolean,
    default: false,
  },
  variants: {
    type: Array,
    default: () => [],
  },
  selectedVariant: {
    type: Object,
    default: () => {},
  },
  activeVariant: {
    type: String,
    default: '',
  },
  contentContainerStyle: {
    type: Object,
    default: () => ({}),
  },
})
const emit = defineEmits([
  'update:name',
  'update:description',
  'update:systemName',
  'activateVariant',
  'addVariant',
  'deleteVariant',
  'selectVariant',
  'updateVariantProperty',
])
</script>
