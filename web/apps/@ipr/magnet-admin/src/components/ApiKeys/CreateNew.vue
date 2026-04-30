<template>
  <km-dialog :model-value="showNewDialog" @cancel="onCancel" @hide="onCancel">
    <km-card class="card-style" style="min-inline-size: 800px">
      <div class="km-card-section card-section-style pb-0">
        <div class="cluster">
          <div class="flex-1">
            <div class="km-heading-7">{{ m.dialog_createApiKey() }}</div>
          </div>
          <div class="flex-none">
            <km-btn icon="close" flat dense @click="onCancel" />
          </div>
        </div>
      </div>
      <div class="km-card-section card-section-style mb-md">
        <div v-if="step === 0" class="stack" data-gap="0">
          <form @submit.prevent="create">
            <km-notification-text class="mb-lg" :notification="m.hint_createApiKey()" />
            <div class="km-field text-secondary-text pl-sm mb-xs">{{ m.common_name() }}</div>
            <div class="full-width">
              <km-input ref="nameRef" v-model="name" data-test="name-input" :placeholder="m.apiKeys_myTestApiKey()" autofocus />
            </div>
            <div class="cluster mt-lg">
              <div class="flex-none">
                <km-btn data-test="cancel-btn" flat :label="m.common_cancel()" tone="brand" @click="onCancel" />
              </div>
              <div class="km-space" />
              <div class="flex-none center-flex-y mr-sm">
                <km-loader v-if="loading" size="20px" />
              </div>
              <div class="flex-none" data-test="create-btn" :data-disabled="loading || !name ? &quot;true&quot; : &quot;false&quot;">
                <km-btn :label="m.dialog_createApiKey()" :disable="loading || !name" @click="create" />
              </div>
            </div>
          </form>
        </div>
        <div v-if="step === 1" class="stack" data-gap="0">
          <km-notification-text class="mb-lg" :notification="m.hint_secretKeyOnce()" />
          <div class="cluster" data-gap="sm" data-wrap="no">
            <div class="km-field text-secondary-text pl-sm" style="white-space: nowrap">{{ name || 'Key' }}</div>
            <div class="full-width">
              <km-input ref="keyRef" v-model="key" :placeholder="m.apiKeys_myTestApiKey()" readonly />
            </div>
            <km-btn :label="m.common_copy()" dense flat icon="copy" icon-size="16px" @click="copyKey" />
          </div>
          <div class="cluster mt-lg">
            <div class="km-space" />
            <div class="flex-none">
              <km-btn data-test="done-btn" :label="m.common_done()" @click="onCancel" />
            </div>
          </div>
        </div>
      </div>
    </km-card>
  </km-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { copyToClipboard } from '@ds/utils/clipboard'
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
  if (!name.value || loading.value) return
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
