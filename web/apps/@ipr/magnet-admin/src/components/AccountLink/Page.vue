<template>
  <div class="cluster overflow-hidden full-height" data-wrap="no">
    <km-scroll-area class="fit">
      <div class="flex full-height fit" style="justify-content: center; flex-wrap: nowrap">
        <div class="flex-none collection-container full-width" style="max-width: 720px">
          <div class="full-height pb-md relative-position px-md mt-lg">
            <div class="km-heading-6 mb-md">{{ m.accountLink_pageTitle() }}</div>

            <!-- ── Step 1: Enter pairing code ─────────────────────────── -->
            <section
              v-if="!preview"
              class="ba-border border-radius-12 bg-white p-lg mb-lg"
            >
              <div class="km-heading-7 mb-sm">{{ m.accountLink_step1_heading() }}</div>
              <p class="km-description text-secondary-text mb-md">{{ m.accountLink_step1_hint() }}</p>
              <div class="cluster" data-gap="md" data-wrap="no">
                <km-input
                  v-model="code"
                  :placeholder="m.accountLink_codePlaceholder()"
                  data-test="account-link-code-input"
                  :disable="loadingPreview"
                  @keyup.enter="onPreview"
                />
                <km-btn
                  data-test="account-link-preview-btn"
                  :label="loadingPreview ? m.accountLink_continueLoading() : m.accountLink_continueBtn()"
                  :disable="!code.trim() || loadingPreview"
                  @click="onPreview"
                />
              </div>
              <div v-if="errorMessage" class="km-description text-negative mt-md">{{ errorMessage }}</div>
            </section>

            <!-- ── Step 2: Confirm binding ────────────────────────────── -->
            <section
              v-else
              class="ba-border border-radius-12 bg-white p-lg mb-lg"
            >
              <div class="km-heading-7 mb-md">{{ m.accountLink_confirmHeading() }}</div>
              <p class="km-description text-secondary-text mb-md">{{ m.accountLink_confirmHint() }}</p>
              <dl class="mb-md">
                <div class="cluster mb-sm" data-gap="md">
                  <dt class="km-description text-secondary-text" style="min-width: 160px">{{ m.accountLink_providerLabel() }}</dt>
                  <dd class="km-description">{{ preview.provider }}</dd>
                </div>
                <div v-if="preview.channel_kind" class="cluster mb-sm" data-gap="md">
                  <dt class="km-description text-secondary-text" style="min-width: 160px">{{ m.accountLink_channelLabel() }}</dt>
                  <dd class="km-description">{{ preview.channel_kind }}</dd>
                </div>
                <div v-if="preview.display_name" class="cluster mb-sm" data-gap="md">
                  <dt class="km-description text-secondary-text" style="min-width: 160px">{{ m.accountLink_displayNameLabel() }}</dt>
                  <dd class="km-description">{{ preview.display_name }}</dd>
                </div>
                <div v-if="preview.email" class="cluster mb-sm" data-gap="md">
                  <dt class="km-description text-secondary-text" style="min-width: 160px">{{ m.accountLink_emailLabel() }}</dt>
                  <dd class="km-description">{{ preview.email }}</dd>
                </div>
                <div v-if="extraEntries.length" class="cluster mb-sm" data-gap="md">
                  <dt class="km-description text-secondary-text" style="min-width: 160px">{{ m.accountLink_additionalLabel() }}</dt>
                  <dd class="km-description">
                    <div v-for="[k, v] in extraEntries" :key="k">
                      <strong>{{ k }}:</strong> {{ v }}
                    </div>
                  </dd>
                </div>
                <div class="cluster" data-gap="md">
                  <dt class="km-description text-secondary-text" style="min-width: 160px">{{ m.accountLink_expiresLabel() }}</dt>
                  <dd class="km-description">{{ formatExpiresAt(preview.expires_at) }}</dd>
                </div>
              </dl>
              <div class="cluster" data-gap="md" data-justify="end">
                <km-btn
                  flat
                  data-test="account-link-cancel-btn"
                  :label="m.common_cancel()"
                  :disable="confirming"
                  @click="onCancel"
                />
                <km-btn
                  data-test="account-link-confirm-btn"
                  :label="confirming ? m.accountLink_confirmLoading() : m.accountLink_confirmBtn()"
                  :disable="confirming"
                  @click="onConfirm"
                />
              </div>
              <div v-if="errorMessage" class="km-description text-negative mt-md">{{ errorMessage }}</div>
            </section>

            <!-- ── My linked accounts ─────────────────────────────────── -->
            <section class="ba-border border-radius-12 bg-white p-lg">
              <div class="cluster mb-md" data-justify="between">
                <div class="km-heading-7">{{ m.accountLink_listHeading() }}</div>
                <km-btn
                  flat
                  data-test="account-link-refresh-btn"
                  :label="m.common_refresh ? m.common_refresh() : 'Refresh'"
                  :loading="loadingList"
                  @click="reloadList"
                />
              </div>
              <div v-if="loadingList && links.length === 0" class="km-description text-secondary-text">{{ m.accountLink_listLoading() }}</div>
              <div v-else-if="links.length === 0" class="km-description text-secondary-text">{{ m.accountLink_listEmpty() }}</div>
              <div v-else>
                <div
                  v-for="link in links"
                  :key="link.id"
                  class="cluster py-md ba-border-bottom"
                  data-justify="between"
                  data-gap="md"
                >
                  <div>
                    <div class="km-description"><strong>{{ link.provider }}</strong></div>
                    <div class="km-description text-secondary-text">{{ link.account_email || link.account_id }}</div>
                    <div v-if="link.created_at" class="km-description text-secondary-text" style="font-size: 0.85em">
                      {{ m.accountLink_linkedOn({ date: formatDate(link.created_at) }) }}
                    </div>
                  </div>
                  <km-btn
                    flat
                    data-test="account-link-revoke-btn"
                    :label="m.accountLink_revokeBtn()"
                    :disable="revokingId === link.id"
                    @click="askRevoke(link)"
                  />
                </div>
              </div>
            </section>

            <!-- ── Revoke confirm dialog ──────────────────────────────── -->
            <km-popup-confirm
              :visible="!!pendingRevoke"
              :confirm-button-label="m.accountLink_revokeConfirmOk()"
              :cancel-button-label="m.common_cancel()"
              notification-icon="warning"
              @confirm="confirmRevoke"
              @cancel="pendingRevoke = null"
            >
              <div class="cluster km-heading-7 mb-md" data-justify="center">{{ m.accountLink_revokeConfirmTitle() }}</div>
              <div class="cluster text-center" data-justify="center">{{ m.accountLink_revokeConfirmBody() }}</div>
              <div v-if="pendingRevoke" class="cluster text-center mt-sm km-description text-secondary-text" data-justify="center">
                {{ pendingRevoke.provider }} — {{ pendingRevoke.account_email || pendingRevoke.account_id }}
              </div>
            </km-popup-confirm>
          </div>
        </div>
      </div>
    </km-scroll-area>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { m } from '@/paraglide/messages'
import {
  confirmAccountLinkCode,
  listLinkedAccounts,
  previewAccountLinkCode,
  revokeLinkedAccount,
  type AccountLinkPreview,
  type LinkedAccount,
} from '@/api/accountLink'

const code = ref('')
const preview = ref<AccountLinkPreview | null>(null)
const links = ref<LinkedAccount[]>([])

const loadingPreview = ref(false)
const confirming = ref(false)
const loadingList = ref(false)
const revokingId = ref<string | null>(null)
const pendingRevoke = ref<LinkedAccount | null>(null)

const errorMessage = ref<string | null>(null)

const extraEntries = computed(() => {
  const extra = preview.value?.extra
  if (!extra) return [] as Array<[string, unknown]>
  return Object.entries(extra)
})

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'message' in err) {
    return String((err as { message: string }).message)
  }
  return m.accountLink_genericError()
}

function formatExpiresAt(iso: string): string {
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString() } catch { return iso }
}

async function reloadList() {
  loadingList.value = true
  try {
    links.value = await listLinkedAccounts()
  } catch (err) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingList.value = false
  }
}

async function onPreview() {
  const trimmed = code.value.trim()
  if (!trimmed) return
  errorMessage.value = null
  loadingPreview.value = true
  try {
    preview.value = await previewAccountLinkCode(trimmed)
  } catch (err) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingPreview.value = false
  }
}

async function onConfirm() {
  if (!preview.value) return
  errorMessage.value = null
  confirming.value = true
  try {
    await confirmAccountLinkCode(preview.value.code)
    preview.value = null
    code.value = ''
    await reloadList()
  } catch (err) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    confirming.value = false
  }
}

function onCancel() {
  preview.value = null
  errorMessage.value = null
}

function askRevoke(link: LinkedAccount) {
  pendingRevoke.value = link
}

async function confirmRevoke() {
  const link = pendingRevoke.value
  pendingRevoke.value = null
  if (!link) return
  errorMessage.value = null
  revokingId.value = link.id
  try {
    await revokeLinkedAccount(link.id)
    await reloadList()
  } catch (err) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    revokingId.value = null
  }
}

onMounted(() => { reloadList() })
</script>
