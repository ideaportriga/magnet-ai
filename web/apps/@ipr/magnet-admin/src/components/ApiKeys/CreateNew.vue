<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='onCancel', @hide='onCancel')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style.q-pb-none
      .row
        .col
          .km-heading-7 New API Key
        .col-auto
          q-btn(icon='close', flat, dense, @click='onCancel')
    q-card-section.card-section-style.q-mb-md
      .column(v-if='step === 0')
        km-notification-text.q-mb-lg(notification='Create new API Key to access Magnet AI')
        .km-field.text-secondary-text.q-pl-8.q-mb-xs Name
        .full-width
          km-input(placeholder='My Test API Key', v-model='name', ref='nameRef')
        .row.q-mt-lg
          .col-auto
            km-btn(flat, label='Cancel', color='primary', @click='onCancel')
          .col
          .col-auto.center-flex-y.q-mr-sm
            q-spinner(v-if='loading', color='primary', size='20px')
          .col-auto
            km-btn(label='Create API Key', @click='create', :disable='loading || !name')
      .column(v-if='step === 1')
        km-notification-text.q-mb-lg(
          notification='For security reasons, this secret key is only displayed once and you won’t be able to view it again. Copy and save the key to a secure destination. If you lose this secret key, you will need to generate a new one.'
        )
        .row.q-gap-8.no-wrap.items-center
          .km-field.text-secondary-text.q-pl-8(style='white-space: nowrap') {{ name || 'Key' }}
          .full-width
            km-input(placeholder='My Test API Key', v-model='key', ref='keyRef', readonly)
          km-btn(label='Copy', @click='copyKey', dense, flat, icon='fa fa-copy', iconSize='16px')
        .row.q-mt-lg
          q-space
          .col-auto
            km-btn(label='Done', @click='onCancel')
</template>

<script setup>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'
import { useStore } from 'vuex'
import { useQuasar, copyToClipboard } from 'quasar'

const { create: createApiKey } = useChroma('api_keys')

const store = useStore()
const name = ref('')
const loading = ref(false)
const key = ref('')
const step = ref(0)
const q = useQuasar()

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

const create = () => {
  loading.value = true
  createApiKey({ name: name.value })
    .then((data) => {
      step.value = 1
      key.value = data.api_key
    })
    .catch((error) => {
      console.log(error)
      q.notify({
        position: 'top',
        message: 'Error creating API Key',
        color: 'negative',
        textColor: 'black',
        timeout: 1000,
      })
    })
    .finally(() => {
      loading.value = false
    })
}

const copyKey = () => {
  copyToClipboard(key.value)
  q.notify({
    position: 'top',
    message: 'Key has been copied to clipboard',
    color: 'positive',
    textColor: 'black',
    timeout: 1000,
  })
}

const onCancel = () => {
  step.value = 0
  name.value = ''
  key.value = ''
  emit('cancel')
}
</script>
