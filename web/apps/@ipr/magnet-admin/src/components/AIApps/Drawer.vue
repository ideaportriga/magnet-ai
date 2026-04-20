<template lang="pug">
km-drawer-layout(storageKey='drawer-ai-apps-preview', :defaultWidth='520', :maxWidth='1200', noScroll)
  template(#header)
    .row
      .col {{ m.common_preview() }}
      .col-auto
  .col.relative-position.full-height
    iframe.absolute-full(
      v-if='iframeSrc',
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
import { m } from '@/paraglide/messages'
import { useState } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
export default {
  setup() {
    const tab = ref('')
    const iframe = ref(null)
    const loading = useState('globalLoading')
    const { draft } = useEntityDetail('ai_apps')

    return { m, loading, tab, iframe, draft }
  },
  computed: {
    baseUrl() {
      let panel = this.$appConfig?.panel?.baseUrl || ''
      if (!panel.startsWith('http')) {
        panel = `https://${panel}`
      }
      let admin = this.$appConfig?.admin?.baseUrl || ''
      if (!admin.startsWith('http')) {
        admin = `https://${admin}`
      }

      return { admin, panel }
    },
    app() {
      return this.draft
    },
    iframeSrc() {
      let panelUrl = `${this.$appConfig?.panel?.baseUrl}/#/?ai_app=${this.app?.system_name}`

      if (panelUrl.startsWith('/')) {
        panelUrl = `${window.location.origin}${panelUrl}`
      }

      return panelUrl
    },
  },
  watch: {
    iframeSrc(val) {
      if (!this.$refs.iframe) return
      this.$refs.iframe.src = val
      this.$refs.iframe.contentWindow?.location.reload()
    },
    app: {
      immediate: true,
      deep: true,
      handler(val) {
        if (val) {
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
    // §B.4 — bind the listener to a property so beforeUnmount can detach it.
    // Anonymous inline listener leaked on every drawer open.
    this._onWindowMessage = (event) => {
      if (event.origin !== this.baseUrl.panel && event.origin !== window.location.origin) return
      if (event.data.type === 'reload_app') {
        this.sendMessage({ app: JSON.stringify(this.app) })
      }
      if (event.data.type === 'reload_iframe') {
        const currentSrc = this.$refs.iframe?.src
        if (!currentSrc) return
        this.$refs.iframe.src = ''
        setTimeout(() => {
          if (this.$refs.iframe) {
            this.$refs.iframe.src = currentSrc
          }
        }, 100)
      }
    }
    window.addEventListener('message', this._onWindowMessage)
  },
  beforeUnmount() {
    if (this._onWindowMessage) {
      window.removeEventListener('message', this._onWindowMessage)
      this._onWindowMessage = null
    }
  },
  methods: {
    sendMessage(data) {
      this.$refs.iframe?.contentWindow?.postMessage(data, this.$appConfig?.panel?.baseUrl)
    },
    handleMessage(event) {
      if (event.data === 'reload') {
        location.reload()
      }
    },
  },
}
</script>
