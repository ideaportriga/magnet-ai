<template lang="pug">
.column.q-pa-16.bg-white.fit.bl-border.height-100.fit(v-if='!!selectedRow', style='min-width: 500px; max-width: 500px')
  .col-auto
    .row.items-center
      .km-heading-7.q-mb-xs Chunk details
  q-separator.q-mb-md
  .col-auto(v-if='selectedRow?.source')
    .col.center-flex-y
      .km-heading-4
    .col-auto.center-flex-y
      km-btn(icon='fas fa-external-link-alt', label='View document', iconSize='16px', flat, @click='openDocument')
  .col
    q-scroll-area.fit
      .row.justify-between.q-pt-8.q-pl-8.q-pr-24
        .col-12.q-py-8
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Title
          km-input(:model-value='selectedRow?.metadata.title ?? "-"', :readonly='true', autogrow)
        .col-12.q-py-8
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
          km-input(:model-value='selectedRow?.metadata.type ?? "-"', :readonly='true')
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
          km-input(:model-value='selectedRow?.metadata?.createdTime ?? "-"', :readonly='true')
        .col-6.q-py-8.q-pl-8
          .km-field.text-secondary-text.q-pl-8 Modified
          km-input(:model-value='selectedRow?.metadata?.modifiedTime ?? "-"', :readonly='true')
</template>
<script>
import { defineComponent, ref } from 'vue'
import { useChroma } from '@shared'

export default defineComponent({
  props: ['selectedRow'],
  setup() {
    const { selected, config, ...useDocuments } = useChroma('documents')
    return {
      selected,
      config,
      useDocuments,
      indexedContentExpanded: ref(false),
      retrievalContentExpanded: ref(false),
      unmodifiedContentExpanded: ref(false),
    }
  },
  computed: {
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
      if (!this.selectedRow) return '{}'
      //return JSON.stringify(this.selectedRow?.metadata, null, 2)
      const { config } = this
      const metaKeys = Object.keys(this.selectedRow?.metadata).filter((key) => {
        const currentConfig = config[key]
        if (!currentConfig) return true
        return currentConfig.fromMetadata
      })
      const localMeta = {}
      metaKeys.forEach((key) => {
        localMeta[key] = this.selectedRow?.metadata[key]
      })
      if (!localMeta) return '{}'
      return JSON.stringify(localMeta, null, 2)
    },
  },
  methods: {
    openDocument() {
      if (this.selectedRow && this.selectedRow?.source) {
        window.open(this.selectedRow?.source, '_blank')
      } else {
        console.error('Document source URL is undefined.')
      }
    },
  },
})
</script>
