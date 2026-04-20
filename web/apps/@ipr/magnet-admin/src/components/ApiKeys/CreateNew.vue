<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='onCancel', @hide='onCancel')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style.q-pb-none
      .row
        .col
          .km-heading-7 {{ m.dialog_createApiKey() }}
        .col-auto
          q-btn(icon='close', flat, dense, @click='onCancel')
    q-card-section.card-section-style.q-mb-md
      .column(v-if='step === 0')
        km-notification-text.q-mb-lg(:notification='m.hint_createApiKey()')
        .km-field.text-secondary-text.q-pl-8.q-mb-xs {{ m.common_name() }}
        .full-width
          km-input(data-test='name-input', :placeholder='m.apiKeys_myTestApiKey()', v-model='name', ref='nameRef')
        .row.q-mt-lg
          .col-auto
            km-btn(data-test='cancel-btn', flat, :label='m.common_cancel()', color='primary', @click='onCancel')
          .col
          .col-auto.center-flex-y.q-mr-sm
            q-spinner(v-if='loading', color='primary', size='20px')
          .col-auto(data-test='create-btn', :data-disabled='loading || !name ? "true" : "false"')
            km-btn(:label='m.dialog_createApiKey()', @click='create', :disable='loading || !name')
      .column(v-if='step === 1')
        km-notification-text.q-mb-lg(
          :notification='m.hint_secretKeyOnce()'
        )
        .row.q-gap-8.no-wrap.items-center
          .km-field.text-secondary-text.q-pl-8(style='white-space: nowrap') {{ name || 'Key' }}
          .full-width
            km-input(:placeholder='m.apiKeys_myTestApiKey()', v-model='key', ref='keyRef', readonly)
          km-btn(:label='m.common_copy()', @click='copyKey', dense, flat, icon='fa fa-copy', iconSize='16px')
        .row.q-mt-lg
          q-space
          .col-auto
            km-btn(:label='m.common_done()', @click='onCancel')
</template>

<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { copyToClipboard } from 'quasar'
import { notify } from '@shared/utils/notify'
import { useSafeMutation } from '@/composables/useSafeMutation'

const queries = useEntityQueries()
const createApiKey = useSafeMutation(queries.api_keys.useCreate(), {
  errorMessage: 'Error creating API Key',
})

const name = ref('')
const loading = ref(false)
const key = ref('')
const step = ref(0)


const props = defineProps({
  showNewDialog: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['cancel'])

const title = computed(() => {
  return step.value === 0 ? 'New API Key' : 'API Key Successfully Created'
})

const create = async () => {
  loading.value = true
  const { success, data } = await createApiKey.run({ name: name.value })
  loading.value = false
  if (!success || !data) return
  step.value = 1
  key.value = data.api_key
}

const copyKey = () => {
  copyToClipboard(key.value)
  notify.copied()
}

const onCancel = () => {
  step.value = 0
  name.value = ''
  key.value = ''
  emit('cancel')
}
</script>
