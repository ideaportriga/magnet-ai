<template>
  <div class="cluster overflow-hidden full-height" data-wrap="no">
    <km-scroll-area class="fit">
      <div class="flex full-height fit" style="justify-content: center; flex-wrap: nowrap">
        <div class="flex-none collection-container full-width" style="max-width: 960px">
          <div class="full-height pb-md relative-position px-md mt-lg">
            <div class="km-heading-6 mb-md">{{ m.accountLinkAdmin_pageTitle() }}</div>

            <!-- ── Filter bar ─────────────────────────────────────────── -->
            <section class="ba-border border-radius-12 bg-white p-lg mb-lg">
              <div class="cluster" data-gap="md" data-wrap="no">
                <div class="basis-2">
                  <km-input
                    v-model="userIdInput"
                    :placeholder="m.accountLinkAdmin_userIdPlaceholder()"
                    :label="m.accountLinkAdmin_userIdLabel()"
                    data-test="account-link-admin-user-id"
                    @keyup.enter="applyFilter"
                  />
                </div>
                <km-btn
                  data-test="account-link-admin-apply"
                  :label="m.accountLinkAdmin_applyFilter()"
                  :loading="loadingList"
                  @click="applyFilter"
                />
                <km-btn
                  flat
                  data-test="account-link-admin-clear"
                  :label="m.accountLinkAdmin_clearFilter()"
                  :disable="!userIdInput && !appliedUserId"
                  @click="clearFilter"
                />
              </div>
            </section>

            <!-- ── List ───────────────────────────────────────────────── -->
            <section class="ba-border border-radius-12 bg-white p-lg">
              <div v-if="loadingList && rows.length === 0" class="km-description text-secondary-text">
                {{ m.accountLinkAdmin_listLoading() }}
              </div>
              <div v-else-if="rows.length === 0" class="km-description text-secondary-text">
                {{ m.accountLinkAdmin_listEmpty() }}
              </div>
              <div v-else>
                <div
                  v-for="row in rows"
                  :key="row.id"
                  class="cluster py-md ba-border-bottom"
                  data-justify="between"
                  data-gap="md"
                >
                  <div>
                    <div class="km-description"><strong>{{ row.provider }}</strong></div>
                    <div class="km-description text-secondary-text">
                      {{ row.account_email || row.account_id }}
                    </div>
                    <div v-if="row.created_at" class="km-description text-secondary-text" style="font-size: 0.85em">
                      {{ m.accountLink_linkedOn({ date: formatDate(row.created_at) }) }}
                    </div>
                  </div>
                  <km-btn
                    flat
                    data-test="account-link-admin-revoke"
                    :label="m.accountLink_revokeBtn()"
                    :disable="revokingId === row.id"
                    @click="askRevoke(row)"
                  />
                </div>
              </div>
              <div v-if="errorMessage" class="km-description text-negative mt-md">
                {{ errorMessage }}
              </div>
            </section>

            <km-popup-confirm
              :visible="!!pendingRevoke"
              :confirm-button-label="m.accountLink_revokeConfirmOk()"
              :cancel-button-label="m.common_cancel()"
              notification-icon="warning"
              @confirm="confirmRevoke"
              @cancel="pendingRevoke = null"
            >
              <div class="cluster km-heading-7 mb-md" data-justify="center">
                {{ m.accountLinkAdmin_revokeConfirmTitle() }}
              </div>
              <div class="cluster text-center" data-justify="center">
                {{ m.accountLinkAdmin_revokeConfirmBody() }}
              </div>
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
import { onMounted, ref } from 'vue'
import { m } from '@/paraglide/messages'
import {
  adminListLinkedAccounts,
  adminRevokeLinkedAccount,
  type AdminLinkedAccount,
} from '@/api/adminAccountLink'

const userIdInput = ref('')
const appliedUserId = ref<string | null>(null)
const rows = ref<AdminLinkedAccount[]>([])
const loadingList = ref(false)
const revokingId = ref<string | null>(null)
const pendingRevoke = ref<AdminLinkedAccount | null>(null)
const errorMessage = ref<string | null>(null)

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'message' in err) {
    return String((err as { message: string }).message)
  }
  return m.accountLink_genericError()
}

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString() } catch { return iso }
}

async function reload() {
  loadingList.value = true
  errorMessage.value = null
  try {
    rows.value = await adminListLinkedAccounts(appliedUserId.value || undefined)
  } catch (err) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingList.value = false
  }
}

async function applyFilter() {
  appliedUserId.value = userIdInput.value.trim() || null
  await reload()
}

async function clearFilter() {
  userIdInput.value = ''
  appliedUserId.value = null
  await reload()
}

function askRevoke(row: AdminLinkedAccount) {
  pendingRevoke.value = row
}

async function confirmRevoke() {
  const row = pendingRevoke.value
  pendingRevoke.value = null
  if (!row) return
  errorMessage.value = null
  revokingId.value = row.id
  try {
    await adminRevokeLinkedAccount(row.id)
    await reload()
  } catch (err) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    revokingId.value = null
  }
}

onMounted(() => { reload() })
</script>
