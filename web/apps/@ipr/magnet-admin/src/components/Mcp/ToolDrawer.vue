<template lang="pug">
.column.bg-white.fit.bl-border.height-100.fit(style='min-width: 500px; max-width: 500px')
  .col.q-pt-16
    .row.no-wrap.full-width.q-px-16
      q-tabs.bb-border.full-width(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        active-bg-color='white',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
        .fit
    .column.fit
      q-scroll-area.fit.q-px-16.q-py-32
        template(v-if='tab == "details"')
          .column.fit
            .col.fit(v-if='selectedRow')
              .row.justify-between
                .col-12.q-py-8
                  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
                  km-input(:model-value='selectedRow.name', readonly)
                .col-12.q-py-8
                  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
                  km-input(v-model='selectedRow.description', type='textarea', rows='1', autogrow, readonly)
                .col-12.q-py-8
                  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
                  km-input(:model-value='selectedRow.type', readonly)
        template(v-if='tab == "test"')
          .bg-white.fit.height-100.fit.q-pb-32
            .col-auto
              .row.items-center.justify-between
                .km-heading-7.q-mb-16 Inputs
              .column.fit
                km-codemirror(
                  v-model='inputParametersString',
                  :style='{ minHeight: "150px" }',
                  :options='{ mode: "application/json" }',
                  language='json'
                )
              .row.justify-end.full-width
                q-btn.q-my-6.border-radius-6(color='primary', @click='testMcpTool', :disable='processing', unelevated, padding='7px 8px')
                  template(v-slot:default)
                    q-icon(name='fas fa-paper-plane', size='16px')
            template(v-if='processing')
              .column.justify-center.items-center
                q-spinner-dots(size='62px', color='primary')

            .col-auto
              .row.items-center.justify-between
                .km-heading-7.q-mb-16 Outputs
              .column.fit(v-if='output')
                km-codemirror(
                  :model-value='JSON.stringify(output, null, 2)',
                  :style='{ minHeight: "150px" }',
                  :options='{ mode: "application/json" }',
                  language='json',
                  readonly
                )
</template>
<script>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
export default {
  props: {
    selectedRow: {
      type: Object,
      required: true,
    },
  },
  setup() {
    const route = useRoute()
    return {
      processing: ref(false),
      inputParametersString: ref('{}'),
      output: ref(''),
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: 'Input Details' },
        { name: 'test', label: 'Test MCP Tool' },
      ]),
      route,
    }
  },

  computed: {
    tool() {
      return this.$store.getters.mcp_tool(this.route.params.name)
    },
  },
  watch: {},
  methods: {
    setTab(tab) {
      this.tab = tab
    },
    regulateTabs(parentTab) {
      if (parentTab === 'definition') {
        this.tab = 'test'
        this.tabs = [{ name: 'test', label: 'Test MCP Tool' }]
      } else {
        this.tabs = [
          { name: 'details', label: 'Input Details' },
          { name: 'test', label: 'Test MCP Tool' },
        ]
      }
    },
    async testMcpTool() {
      if (this.processing) {
        return
      }

      let input = {}

      try {
        input = JSON.parse(this.inputParametersString)
      } catch (e) {
        console.log('err', e)
        this.$store.commit('set', {
          errorMessage: {
            technicalError: e,
            text: `Input is not a valid JSON`,
          },
        })

        return
      }

      this.processing = true
      try {
        const res = await this.$store.dispatch('callMcpTool', {
          tool_name: this.tool.name,
          input,
        })

        console.log('res ', res)

        this.output = res
      } catch (e) {
        this.output = null
      } finally {
        this.processing = false
      }
    },
  },
}
</script>
