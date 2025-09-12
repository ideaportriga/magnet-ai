<template lang="pug">
.bg-white.full-height.column.no-wrap
  .col-auto.km-heading-7.q-pt-16.q-px-16
    .row
      .col Preview
      .col-auto
  .q-mb-16.q-px-16
    q-separator
  .col.relative-position.full-height
    iframe.absolute-full(
      :src='iframeSrc',
      width='100%',
      height='100%',
      frameborder='0',
      allowfullscreen,
      ref='iframe',
      :style='{ zIndex: 10 }',
      allow='clipboard-write'
    )
    .flex.absolute-center(:style='{ zIndex: 5 }')
      q-spinner-dots(size='62px', color='primary')
</template>

<script>
import { ref } from 'vue'
import { useState } from '@shared'
export default {
  setup() {
    const tab = ref('')
    const iframe = ref(null)
    const loading = useState('globalLoading')
    const panelOpenBlock = useState('panelOpenBlock')

    return { loading, panelOpenBlock, tab, iframe }
  },
  computed: {
    baseUrl() {
      let panel = this.$store.getters.config?.panel?.baseUrl || ''
      if (!panel.startsWith('http')) {
        panel = `https://${panel}`
      }
      let admin = this.$store.getters.config?.admin?.baseUrl || ''
      if (!admin.startsWith('http')) {
        admin = `https://${admin}`
      }

      return { admin, panel }
    },
    app() {
      return this.$store.getters.ai_app
    },
    iframeSrc() {
      const url = this.baseUrl.panel //window.location.origino
      return `${url}/#/?ai_app=${this.app?.system_name}&iframe=true`
    },
  },
  watch: {
    iframeSrc(val) {
      this.$refs.iframe.src = val
      this.$refs.iframe.contentWindow.location.reload()
    },
    app: {
      immediate: true,
      deep: true,
      handler(val) {
        if (val) {
          //localStorage.setItem('iframe_ai_app', JSON.stringify(val))
          this.sendMessage({ app: JSON.stringify(val) })
        }
      },
    },
    loading: {
      immediate: true,
      handler(val) {
        if (val) {
          this.$q.loading.show()
        } else {
          this.$q.loading.hide()
        }
      },
    },
    panels: {
      immediate: true,
      handler(val) {
        this.tab = (val || [])?.[0]?.name
      },
    },
  },
  mounted() {
    window.addEventListener('message', (event) => {
      if (event.origin !== this.baseUrl.panel) return
      if (event.data.type === 'reload_app') {
        this.sendMessage({ app: JSON.stringify(this.app) })
      }
    })
  },

  // beforeUnmount() {
  //   // Clean up the event listener when the component is destroyed
  //   window.removeEventListener('message', this.handleMessage)
  // },
  methods: {
    sendMessage(data) {
      this.$refs.iframe?.contentWindow.postMessage(data, this.$store.getters.config?.panel?.baseUrl)
    },
    handleMessage(event) {
      // Ensure the message is coming from the correct origin
      if (event.data === 'reload') {
        console.log('reload')
        location.reload()
      }
    },
  },
}
</script>
