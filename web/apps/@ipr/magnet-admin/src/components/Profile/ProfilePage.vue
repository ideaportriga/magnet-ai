<template>
  <layouts-details-layout no-header>
    <template #content>
      <km-tabs v-model="tab">
        <km-tab name="profile" :label="m.user_profile()" />
        <km-tab name="access" :label="m.common_access()" />
        <km-tab name="security" :label="m.user_security()" />
      </km-tabs>
      <div class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="min-block-size: 0">
        <div class="cluster full-height full-width" data-gap="lg">
          <div class="flex-1 full-height full-width">
            <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
              <div class="flex-none full-width">
                <template v-if="tab === &quot;profile&quot;">
                  <km-section :title="m.section_account()" :sub-title="m.subtitle_yourAccount()">
                    <div class="cluster gap-lg">
                      <div class="flex-1">
                        <div class="km-input-label">{{ m.common_name() }}</div>
                        <km-input :model-value="editName" :placeholder="m.profile_yourName()" @input="editName = $event" />
                      </div>
                      <div class="flex-1">
                        <div class="km-input-label">{{ m.auth_email() }}</div>
                        <km-input :model-value="displayEmail" readonly />
                      </div>
                    </div>
                    <div class="mt-md">
                      <div class="km-input-label">{{ m.user_lastLogin() }}</div>
                      <div class="km-description mt-xs">{{ userInfo?.last_login_at ? new Date(userInfo.last_login_at).toLocaleString() : m.user_na() }}</div>
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />
                  <km-section :title="m.section_linkedAccounts()" :sub-title="m.subtitle_linkedIdentityProviders()">
                    <template v-if="oauthAccounts.length">
                      <div class="stack" data-gap="sm" style="max-inline-size: 400px">
                        <div v-for="account in oauthAccounts" :key="account.provider" class="cluster p-sm pl-md ba-border border-radius-8" data-wrap="no">
                          <km-glyph class="mr-sm" name="check" size="16px" tone="success" />
                          <div class="km-title mr-md">{{ providerLabel(account.provider) }}</div>
                          <div v-if="account.email" class="km-description text-grey">{{ account.email }}</div>
                        </div>
                      </div>
                    </template>
                    <div v-else class="km-description text-grey">{{ m.user_noLinkedAccounts() }}</div>
                  </km-section>
                </template>
                <template v-if="tab === &quot;access&quot;">
                  <!-- Organization-tenant (PR 4 of access-control plan). -->
                  <km-section :title="m.section_organization()" :sub-title="m.subtitle_yourOrganization()">
                    <div v-if="tenant" class="stack p-md ba-border border-radius-8" data-gap="xs" style="max-inline-size: 480px">
                      <div class="cluster" data-gap="sm" data-wrap="no" data-align="center">
                        <km-glyph name="building" size="20px" tone="brand" />
                        <div class="km-title">{{ tenant.name }}</div>
                      </div>
                      <div class="km-description text-grey">
                        <span class="font-mono">{{ tenant.slug }}</span>
                        <span class="mx-xs">·</span>
                        <span class="font-mono text-caption">{{ tenant.id }}</span>
                      </div>
                    </div>
                    <div v-else class="km-description text-grey">{{ m.access_noTenant() }}</div>
                  </km-section>
                  <km-separator class="my-lg" />

                  <!-- Roles with system/custom indicator (PR 2/5a). -->
                  <km-section :title="m.section_roles()" :sub-title="m.subtitle_yourRoles()">
                    <div class="stack" data-gap="sm" style="max-inline-size: 480px">
                      <div v-for="role in rolesDetailed" :key="role.id" class="cluster p-sm pl-md ba-border border-radius-8" data-wrap="no" data-align="center">
                        <km-glyph class="mr-sm" :name="role.is_system ? 'shield-check' : 'user'" size="16px" :tone="role.is_system ? 'brand' : 'neutral'" />
                        <div class="km-title flex-1">{{ role.name || role.slug }}</div>
                        <km-chip
                          :tone="role.is_system ? 'brand' : 'muted'"
                          size="sm"
                          :label="role.is_system ? m.access_roleSystem() : m.access_roleCustom()"
                          data-test="role-kind-chip"
                        />
                      </div>
                      <div v-if="!rolesDetailed.length" class="km-description text-grey">{{ m.access_noRoles() }}</div>
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />

                  <!-- Effective permissions, grouped by resource type (PR 1/2). -->
                  <km-section :title="m.section_permissions()" :sub-title="m.subtitle_yourPermissions()">
                    <div v-if="permissionGroups.length" class="stack" data-gap="md">
                      <div v-for="group in permissionGroups" :key="group.resource" class="stack p-md ba-border border-radius-8" data-gap="xs">
                        <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
                          <km-glyph :name="resourceIcon(group.resource)" size="16px" tone="brand" />
                          <div class="km-title">{{ resourceLabel(group.resource) }}</div>
                          <div class="km-description text-grey">{{ group.codes.length }}</div>
                        </div>
                        <div class="cluster" data-gap="xs" data-wrap="yes">
                          <km-chip
                            v-for="code in group.codes"
                            :key="code"
                            :label="code.split(':')[0]"
                            tone="muted"
                            size="sm"
                          />
                        </div>
                      </div>
                    </div>
                    <div v-else class="km-description text-grey">{{ m.access_noPermissionsAssigned() }}</div>
                    <div class="km-description text-caption text-grey mt-md">
                      {{ m.access_permissionsHint({ count: permissions.length }) }}
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />

                  <!-- Departments (PR 8). -->
                  <km-section :title="m.section_departments()" :sub-title="m.subtitle_yourDepartments()">
                    <div v-if="departments.length" class="stack" data-gap="sm" style="max-inline-size: 480px">
                      <div v-for="dept in departments" :key="dept.id" class="cluster p-sm pl-md ba-border border-radius-8" data-wrap="no" data-align="center">
                        <km-glyph class="mr-sm" name="group" size="16px" tone="brand" />
                        <div class="km-title flex-1">{{ dept.name }}</div>
                        <km-chip v-if="dept.is_lead" tone="brand" size="sm" :label="m.access_departmentLead()" />
                      </div>
                    </div>
                    <div v-else class="km-description text-grey">{{ m.access_noDepartments() }}</div>
                  </km-section>
                  <km-separator class="my-lg" />

                  <!-- Groups. -->
                  <km-section :title="m.section_groups()" :sub-title="m.subtitle_groups()">
                    <div v-if="groups.length" class="stack" data-gap="sm" style="max-inline-size: 480px">
                      <div v-for="grp in groups" :key="grp.id" class="cluster p-sm pl-md ba-border border-radius-8" data-wrap="no" data-align="center">
                        <km-glyph class="mr-sm" name="users" size="16px" tone="muted" />
                        <div class="km-title flex-1">{{ grp.name }}</div>
                        <km-chip v-if="grp.role" tone="muted" size="sm" :label="grp.role" />
                      </div>
                    </div>
                    <div v-else class="km-description text-grey">{{ m.access_noGroups() }}</div>
                  </km-section>
                </template>
                <template v-if="tab === &quot;security&quot;">
                  <km-section :title="m.section_twoFactorAuth()" :sub-title="m.subtitle_addSecurityLayer()">
                    <div class="cluster" data-gap="sm">
                      <div class="km-description">{{ m.common_status() }}:</div>
                      <km-chip :tone="userInfo?.is_two_factor_enabled ? &quot;success&quot; : &quot;neutral&quot;" size="sm">{{ userInfo?.is_two_factor_enabled ? m.common_enabled() : m.common_disabled() }}</km-chip>
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />
                  <km-section :title="m.section_activeSessions()" :sub-title="m.subtitle_activeDevices()">
                    <div v-if="sessions.length &gt; 1" class="cluster mb-sm" data-justify="end">
                      <km-btn flat :label="m.user_revokeAllOthers()" size="sm" @click="revokeAllSessions" />
                    </div>
                    <div class="stack" data-gap="sm">
                      <div v-for="session in sessions" :key="session.id" class="cluster p-md ba-border border-radius-8" data-justify="between">
                        <div class="stack">
                          <div class="km-title">{{ session.device_info || m.user_unknownDevice() }}</div>
                          <div class="km-description text-grey">{{ m.user_since({ date: new Date(session.created_at).toLocaleString() }) }}</div>
                        </div>
                        <km-btn flat :label="m.user_revoke()" size="sm" @click="revokeSession(session.id)" />
                      </div>
                      <div v-if="!sessions.length" class="km-description text-grey">{{ m.user_noActiveSessions() }}</div>
                    </div>
                  </km-section>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </layouts-details-layout>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@shared'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { m } from '@/paraglide/messages'

export default {
  setup() {
    const authStore = useSharedAuthStore()
    const route = useRoute()
    const auth = useAuth()
    const userInfo = computed(() => authStore.userInfo)
    const validTabs = ['profile', 'access', 'security']
    const tab = ref(validTabs.includes(route.params?.tab) ? route.params.tab : 'profile')
    const editName = ref(userInfo.value?.name || '')
    const sessions = ref([])

    const displayEmail = computed(() =>
      userInfo.value?.email || userInfo.value?.preferred_username || ''
    )

    const oauthAccounts = computed(() =>
      userInfo.value?.oauth_accounts || []
    )

    const roles = computed(() =>
      userInfo.value?.roles || []
    )

    // PR 4–8 access-control plan: tenant + detailed roles + permissions +
    // departments + groups. All optional — `/me` ships empty / null values
    // when the user hasn't been migrated onto the new pipeline yet.
    const tenant = computed(() => userInfo.value?.tenant || null)

    const rolesDetailed = computed(() => {
      const detailed = userInfo.value?.roles_detailed
      if (Array.isArray(detailed) && detailed.length) return detailed
      // Fallback when only `roles` (slugs) are available.
      return (userInfo.value?.roles || []).map((slug) => ({
        id: slug,
        slug,
        name: slug,
        is_system: ['admin', 'user', 'viewer'].includes(slug),
      }))
    })

    const permissions = computed(() => userInfo.value?.permissions || [])

    /** Group permission codes by their `resource_type` (before the colon). */
    const permissionGroups = computed(() => {
      const groups = new Map()
      for (const code of permissions.value) {
        const [, resource] = code.split(':')
        if (!resource) continue
        if (!groups.has(resource)) groups.set(resource, [])
        groups.get(resource).push(code)
      }
      return Array.from(groups.entries())
        .map(([resource, codes]) => ({ resource, codes: codes.sort() }))
        .sort((a, b) => a.resource.localeCompare(b.resource))
    })

    const departments = computed(() => userInfo.value?.departments || [])
    const groups = computed(() => userInfo.value?.groups || [])

    onMounted(async () => {
      if (auth.client.value) {
        try {
          sessions.value = await auth.client.value.getSessions()
        } catch (e) {
          // ignore
        }
      }
    })

    return {
      m,
      userInfo,
      tab,
      editName,
      displayEmail,
      oauthAccounts,
      roles,
      rolesDetailed,
      tenant,
      permissions,
      permissionGroups,
      departments,
      groups,
      sessions,
      auth,
    }
  },
  methods: {
    providerLabel(provider) {
      const labels = { microsoft: 'Microsoft', google: 'Google', github: 'GitHub', oracle: 'Oracle' }
      return labels[provider] || provider
    },
    /** Map a permission `resource_type` token to a Phosphor icon name. */
    resourceIcon(resource) {
      const map = {
        agents: 'robot',
        ai_apps: 'apps',
        collections: 'database',
        prompts: 'chat',
        knowledge_graph: 'graph',
        rag_tools: 'wrench',
        retrieval_tools: 'magnifying-glass',
        mcp_servers: 'server',
        api_servers: 'server',
        evaluations: 'check-circle',
        deep_research: 'flask',
        prompt_queue: 'queue',
        files: 'file',
        jobs: 'lightning',
        observability: 'chart',
        note_taker: 'microphone',
        ai_models: 'brain',
        providers: 'plug',
        settings: 'gear',
        roles: 'shield',
        users: 'user-circle',
        groups: 'users',
        api_keys: 'key',
        resource_access: 'lock',
        audit: 'list-magnifying-glass',
      }
      return map[resource] || 'package'
    },
    /** Human-readable label for a resource token. Falls back to a
     *  Title-Case version when no i18n key is registered. */
    resourceLabel(resource) {
      if (!resource) return ''
      return resource
        .split('_')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },
    async revokeSession(id) {
      if (!this.auth.client.value) return
      await this.auth.client.value.revokeSession(id)
      this.sessions = await this.auth.client.value.getSessions()
    },
    async revokeAllSessions() {
      if (!this.auth.client.value) return
      await this.auth.client.value.revokeAllSessions()
      this.sessions = await this.auth.client.value.getSessions()
    },
  },
}
</script>
