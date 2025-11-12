<template lang="pug">
.column.fit
  .col-auto
    .row.items-center
      km-btn(flat, icon='fas fa-chevron-left', @click='$emit("close")', iconSize='20px', color='secondary-text')
      .km-heading-7.q-mb-xs.q-ml-sm Chunk details
  q-separator.q-mb-md
  .col-auto(v-if='selectedRow?.metadata?.source')
    .col.center-flex-y
      .km-heading-4
    .col-auto.center-flex-y
      km-btn(icon='fas fa-external-link-alt', label='View document', iconSize='16px', flat, @click='openDocument')
  .col
    q-scroll-area.fit
      .row.justify-between.q-pt-8.q-pl-8.q-pr-24
        .col-12.q-py-8
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Title
          km-input(:model-value='selectedRow?.metadata?.title ?? "-"', :readonly='true', autogrow)
        .col-12.q-py-8
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
          km-input(:model-value='selectedRow?.metadata?.type ?? "-"', :readonly='true')
        .col-12.q-py-8
          .row.items-center
            .km-field.text-secondary-text.q-pb-xs.q-pl-8.col
              span(
                v-if='(selectedRow?.content == selectedRow?.metadata?.content_override || !selectedRow?.metadata?.content_override) && (selectedRow?.content == selectedRow?.metadata?.content?.retrieval || !selectedRow?.metadata?.content?.retrieval)'
              ) Indexed & retrieval content
              span(v-else) Indexed content
            .col-auto
              q-btn(
                flat,
                ripple='false',
                round,
                color='secondary',
                :icon='indexedContentExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"',
                @click='indexedContentExpanded = !indexedContentExpanded',
                size='xs'
              )
          km-input(:model-value='indexedContent', :readonly='true', autogrow)
        .col-12.q-py-8(v-if='selectedRow?.metadata?.content_override && selectedRow?.content != selectedRow?.metadata?.content_override')
          .row.items-center
            .km-field.text-secondary-text.q-pb-xs.q-pl-8.col Retrieval content
            .col-auto
              q-btn(
                flat,
                ripple='false',
                round,
                color='secondary',
                :icon='retrievalContentExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"',
                @click='retrievalContentExpanded = !retrievalContentExpanded',
                size='xs'
              )
          km-input(:model-value='retrievalContent', :readonly='true', autogrow)
        .col-12.q-py-8(v-else-if='selectedRow?.metadata?.content?.retrieval && selectedRow?.content != selectedRow?.metadata?.content?.retrieval')
          .row.items-center
            .km-field.text-secondary-text.q-pb-xs.q-pl-8.col Retrieval content
            .col-auto
              q-btn(
                flat,
                ripple='false',
                round,
                color='secondary',
                :icon='retrievalContentExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"',
                @click='retrievalContentExpanded = !retrievalContentExpanded',
                size='xs'
              )
          km-input(:model-value='retrievalContent', :readonly='true', autogrow)
        .col-12.q-py-8(
          v-if='selectedRow?.metadata?.content?.unmodified && selectedRow?.content != selectedRow?.metadata?.content?.unmodified && selectedRow?.metadata?.content?.unmodified != selectedRow?.metadata?.content?.retrieval'
        )
          .row.items-center
            .km-field.text-secondary-text.q-pb-xs.q-pl-8.col Original unmodified content
            .col-auto
              q-btn(
                flat,
                ripple='false',
                round,
                color='secondary',
                :icon='unmodifiedContentExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"',
                @click='unmodifiedContentExpanded = !unmodifiedContentExpanded',
                size='xs'
              )
          km-input(:model-value='unmodifiedContent', :readonly='true', autogrow)
        .col-12.q-py-8
          .km-field.text-secondary-text.q-pl-8 Metadata
          km-codemirror.fit(v-model='metadata', :readonly='true')
        .col-6.q-py-8
          .km-field.text-secondary-text.q-pl-8 Created
          km-input(:model-value='selectedRow?.metadata?.modifiedTime ?? "-"', :readonly='true')
        .col-6.q-py-8.q-pl-8
          .km-field.text-secondary-text.q-pl-8 Last synced
          km-input(:model-value='selectedRow?.metadata?.modifiedTime ?? "-"', :readonly='true')
</template>
<script>
import { defineComponent, ref } from 'vue'
import { useChroma } from '@shared'

export default defineComponent({
  props: {
    selectedRow: {
      type: Object,
      default: () => ({}),
    },
  },
  setup() {
    const { config } = useChroma('documents')
    return {
      config,
      indexedContentExpanded: ref(false),
      retrievalContentExpanded: ref(false),
      unmodifiedContentExpanded: ref(false),
    }
  },
  computed: {
    selectedRowMetadata() {
      return this.selectedRow?.metadata ?? {}
    },
    indexedContent() {
      let content = this.selectedRow?.content
      if (!this.indexedContentExpanded) {
        content = content.substring(0, 200)
      }
      return content ?? '-'
    },
    retrievalContent() {
      let content = this.selectedRow?.metadata?.content?.retrieval || this.selectedRow?.metadata?.content_override
      if (!this.retrievalContentExpanded) {
        content = content.substring(0, 200)
      }
      return content ?? '-'
    },
    unmodifiedContent() {
      let content = this.selectedRow?.metadata?.content?.unmodified
      if (!this.unmodifiedContentExpanded) {
        content = content.substring(0, 200)
      }
      return content ?? '-'
    },
    metadata() {
      if (!this.selectedRowMetadata) return '{}'
      const { config } = this
      const metaKeys = Object.keys(this.selectedRowMetadata).filter((key) => {
        const currentConfig = config[key]
        if (!currentConfig) return true
        return currentConfig.fromMetadata
      })
      const localMeta = {}
      metaKeys.forEach((key) => {
        localMeta[key] = this.selectedRowMetadata[key]
      })
      if (!localMeta) return '{}'
      return JSON.stringify(localMeta, null, 2)
    },
  },
  methods: {
    openDocument() {
      if (this.selectedRow && this.selectedRow?.metadata?.source) {
        window.open(this.selectedRow?.metadata?.source, '_blank')
      } else {
        console.error('Document source URL is undefined.')
      }
    },
  },
})
</script>
