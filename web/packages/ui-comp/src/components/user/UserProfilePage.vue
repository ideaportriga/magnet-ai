<template lang="pug">
.q-pa-lg(style='max-width: 600px; margin: 0 auto')
  .text-h5.q-mb-lg {{ t.profile }}

  q-card.q-mb-md
    q-card-section
      .text-subtitle1.q-mb-md {{ t.accountInfo }}
      q-form.q-gutter-sm(@submit.prevent='handleSave')
        q-input(
          v-model='editName',
          :label='t.name',
          outlined,
          dense
        )
        q-input(
          :model-value='userInfo?.email',
          :label='t.email',
          outlined,
          dense,
          readonly
        )
          template(v-slot:append)
            q-icon(v-if='userInfo?.is_verified', name='verified', color='positive', size='20px')
              q-tooltip {{ t.verified }}

        .text-caption.text-grey.q-mt-sm
          | {{ t.lastLogin }} {{ userInfo?.last_login_at ? new Date(userInfo.last_login_at).toLocaleString() : t.na }}

        q-btn.q-mt-sm(
          type='submit',
          color='primary',
          :label='t.save',
          :loading='saving',
          :disable='editName === userInfo?.name',
          no-caps
        )
        .text-positive.text-caption(v-if='saveSuccess') {{ t.saved }}

  //- Linked accounts
  q-card.q-mb-md(v-if='userInfo?.oauth_accounts')
    q-card-section
      .text-subtitle1.q-mb-md {{ t.linkedAccounts }}

      q-list
        q-item(v-for='account in userInfo.oauth_accounts', :key='account.provider')
          q-item-section(side)
            q-icon(name='link', size='20px', color='positive')
          q-item-section
            q-item-label {{ providerLabel(account.provider) }}
            q-item-label(caption) {{ account.email }}

      .text-caption.text-grey.q-mt-sm(v-if='!userInfo.oauth_accounts.length')
        | {{ t.noLinkedAccounts }}
</template>

<script lang="ts">
const DEFAULT_T = {
  profile: 'Profile',
  accountInfo: 'Account info',
  name: 'Name',
  email: 'Email',
  verified: 'Verified',
  lastLogin: 'Last login:',
  na: 'N/A',
  save: 'Save',
  saved: 'Saved',
  linkedAccounts: 'Linked accounts',
  noLinkedAccounts: 'No linked accounts',
  microsoft: 'Microsoft',
  google: 'Google',
  github: 'GitHub',
  oracle: 'Oracle',
}
export default {}
</script>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { UserInfo } from '@shared/auth'

const props = withDefaults(defineProps<{
  userInfo: UserInfo | null
  /** i18n labels — pass translated strings to override English defaults */
  t?: Record<string, string>
}>(), {
  t: () => ({ ...DEFAULT_T }),
})

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const emit = defineEmits<{
  save: [data: { name: string }]
}>()

const editName = ref(props.userInfo?.name || '')
const saving = ref(false)
const saveSuccess = ref(false)

watch(() => props.userInfo?.name, (val) => {
  if (val !== undefined) editName.value = val || ''
})

function providerLabel(provider: string): string {
  const labels: Record<string, string> = { microsoft: t.value.microsoft, google: t.value.google, github: t.value.github, oracle: t.value.oracle }
  return labels[provider] || provider
}

async function handleSave() {
  saving.value = true
  saveSuccess.value = false
  emit('save', { name: editName.value })
  // Parent handles the actual API call; we just show feedback
  setTimeout(() => {
    saving.value = false
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 2000)
  }, 500)
}
</script>
