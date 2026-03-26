<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else)
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 500px')
      .full-height.q-pb-md.relative-position.q-px-md
        //- ── Header: name / description / system_name ────────────────
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col
            .row.items-center
              .col
                km-input-flat.km-heading-4.full-width.text-black(
                  placeholder='Name',
                  :modelValue='recordName',
                  @input='recordName = $event'
                )
            .row.items-center.q-mt-sm
              .col
                km-input-flat.km-description.full-width.text-black(
                  placeholder='Description',
                  :modelValue='recordDescription',
                  @input='recordDescription = $event'
                )
            .row.items-center.q-pl-6.q-mt-sm
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              .col
                km-input-flat.km-description.full-width(
                  placeholder='Enter system name',
                  :modelValue='recordSystemName',
                  @input='recordSystemName = $event'
                )

        //- ── Tabs ────────────────────────────────────────────────────
        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
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
            q-tab(name='general', label='General')
            q-tab(name='prompts', label='Prompts')
            q-tab(name='integrations', label='Integrations')
            q-tab(name='bot', label='Bot Credentials')

          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 360px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  .col-auto.full-width
                    note-taker-tab-general(v-if='tab === "general"')
                    note-taker-tab-prompts(v-if='tab === "prompts"')
                    note-taker-tab-integrations(v-if='tab === "integrations"')
                    note-taker-tab-bot(v-if='tab === "bot"')

  //- ── Right-side drawer (preview) ──────────────────────────────────
  .col-auto
    note-taker-drawer(:settingsId='configId', v-if='configId')
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'

import NoteTakerTabGeneral from './tabs/General.vue'
import NoteTakerTabPrompts from './tabs/Prompts.vue'
import NoteTakerTabIntegrations from './tabs/Integrations.vue'
import NoteTakerTabBot from './tabs/Bot.vue'
import NoteTakerDrawer from './Drawer.vue'

const store = useStore()
const router = useRouter()
const route = useRoute()

const tab = ref('general')

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => store.getters.noteTakerSettingsActiveRecord)
const loading = computed(() => store.getters.noteTakerLoading || !activeRecord.value)
const apiReady = computed(() => Boolean(store.getters.config?.api?.aiBridge?.urlAdmin))

const recordName = computed({
  get: () => activeRecord.value?.name || '',
  set: (value: string) => store.dispatch('updateNoteTakerRecordMeta', { name: value }),
})
const recordDescription = computed({
  get: () => activeRecord.value?.description || '',
  set: (value: string) => store.dispatch('updateNoteTakerRecordMeta', { description: value }),
})
const recordSystemName = computed({
  get: () => activeRecord.value?.system_name || '',
  set: (value: string) => store.dispatch('updateNoteTakerRecordMeta', { system_name: value }),
})

const loadRecord = async () => {
  if (!configId.value || !apiReady.value) return
  const record = await store.dispatch('fetchNoteTakerSettingsById', configId.value)
  if (!record) router.push('/note-taker')
}

watch(apiReady, (ready) => {
  if (!ready) return
  if (!store.getters['chroma/promptTemplates']?.items?.length) {
    store.dispatch('chroma/get', { entity: 'promptTemplates' })
  }
  if (!store.getters['chroma/api_servers']?.items?.length) {
    store.dispatch('chroma/get', { entity: 'api_servers' })
  }
  loadRecord()
}, { immediate: true })

watch(() => configId.value, () => loadRecord())

</script>
