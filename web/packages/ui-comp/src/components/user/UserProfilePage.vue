<script setup lang="ts">
/**
 * User profile page — name + email + linked OAuth accounts. Rewritten on
 * `@ds` (KmInput, KmCard-flavoured panels via custom CSS, KmBtn).
 */

import { computed, ref, watch } from 'vue'
import type { UserInfo } from '@shared/auth'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import KmInput from '@ds/components/domain/KmInput.vue'
import KmTooltip from '@ds/components/domain/KmTooltip.vue'

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

interface OAuthAccount { provider: string; email: string }

const props = withDefaults(
  defineProps<{
    userInfo: UserInfo | null
    t?: Record<string, string>
  }>(),
  { t: () => ({}) },
)

const emit = defineEmits<{ save: [data: { name: string }] }>()

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const editName = ref(props.userInfo?.name || '')
const saving = ref(false)
const saveSuccess = ref(false)

watch(
  () => props.userInfo?.name,
  (val) => {
    if (val !== undefined) editName.value = val || ''
  },
)

function providerLabel(provider: string): string {
  const labels: Record<string, string> = {
    microsoft: t.value.microsoft,
    google: t.value.google,
    github: t.value.github,
    oracle: t.value.oracle,
  }
  return labels[provider] || provider
}

function handleSave() {
  saving.value = true
  saveSuccess.value = false
  emit('save', { name: editName.value })
  setTimeout(() => {
    saving.value = false
    saveSuccess.value = true
    setTimeout(() => {
      saveSuccess.value = false
    }, 2000)
  }, 500)
}

const oauthAccounts = computed<OAuthAccount[]>(() => (props.userInfo?.oauth_accounts as OAuthAccount[]) ?? [])
</script>

<template>
  <div class="user-profile-page">
    <h2 class="user-profile-page__title">{{ t.profile }}</h2>

    <section class="user-profile-page__card stack" data-gap="md">
      <h3 class="user-profile-page__section-title">{{ t.accountInfo }}</h3>

      <form class="stack" data-gap="md" @submit.prevent="handleSave">
        <KmInput v-model="editName" :label="t.name" />

        <div class="user-profile-page__email">
          <KmInput :model-value="userInfo?.email" :label="t.email" readonly>
            <template #append>
              <KmTooltip v-if="userInfo?.is_verified" :label="t.verified">
                <template #trigger>
                  <span class="user-profile-page__verified">
                    <KmGlyph name="check" size="20px" tone="success" />
                  </span>
                </template>
              </KmTooltip>
            </template>
          </KmInput>
        </div>

        <p class="user-profile-page__last-login">
          {{ t.lastLogin }}
          {{ userInfo?.last_login_at ? new Date(userInfo.last_login_at).toLocaleString() : t.na }}
        </p>

        <div>
          <KmBtn
            type="submit"
            :label="t.save"
            :loading="saving"
            :disable="editName === userInfo?.name"
            @click="handleSave"
          />
          <span v-if="saveSuccess" class="user-profile-page__saved">{{ t.saved }}</span>
        </div>
      </form>
    </section>

    <section v-if="userInfo?.oauth_accounts" class="user-profile-page__card stack" data-gap="md">
      <h3 class="user-profile-page__section-title">{{ t.linkedAccounts }}</h3>

      <ul v-if="oauthAccounts.length" class="user-profile-page__accounts">
        <li
          v-for="account in oauthAccounts"
          :key="account.provider"
          class="user-profile-page__account cluster gap-sm"
          data-align="center"
        >
          <KmGlyph name="link" size="20px" tone="success" />
          <span class="user-profile-page__account-meta">
            <span class="user-profile-page__account-name">{{ providerLabel(account.provider) }}</span>
            <span class="user-profile-page__account-email">{{ account.email }}</span>
          </span>
        </li>
      </ul>

      <p v-else class="user-profile-page__last-login">{{ t.noLinkedAccounts }}</p>
    </section>
  </div>
</template>

<style>
.user-profile-page {
  max-inline-size: 600px;
  margin: 0 auto;
  padding: var(--ds-space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
}
.user-profile-page__title {
  font-size: 22px;
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}
.user-profile-page__card {
  padding: var(--ds-space-lg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-white);
}
.user-profile-page__section-title {
  font-size: var(--ds-font-size-body-lg);
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}
.user-profile-page__last-login {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  margin: 0;
}
.user-profile-page__saved {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-success-text);
  padding-inline-start: var(--ds-space-sm);
}
.user-profile-page__verified { display: inline-flex; align-items: center; }

.user-profile-page__accounts {
  list-style: "";
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
}
.user-profile-page__account-meta { display: inline-flex; flex-direction: column; }
.user-profile-page__account-name { font-weight: var(--ds-font-weight-medium); }
.user-profile-page__account-email { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); }
</style>
