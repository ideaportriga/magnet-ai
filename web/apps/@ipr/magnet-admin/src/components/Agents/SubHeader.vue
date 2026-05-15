<template>
  <div>
    <km-separator class="my-sm" />
    <div class="cluster">
      <!-- Variant picker stays interactive even when read-only: switching
           between variants is a *read* action so the user can see how
           each one is configured. -->
      <div class="flex-none py-auto">
        <km-dropdown-select :model-value="selectedVariant" :options="variantOptions" @update:model-value="setSelectedVariant" />
      </div>
      <div class="flex-1 mx-sm">
        <km-input-flat class="km-description full-width" :placeholder="m.common_description()" :model-value="variant_description" :readonly="agentReadonly" @change="variant_description = $event" />
      </div>
      <!-- "Active" badge — always visible (it's a read-only indicator). -->
      <div v-if="isActive" class="flex-none mr-sm">
        <km-chip class="mr-sm" :label="m.common_active()" tone="brand" />
      </div>
      <!-- Activate — write action, hidden when read-only. Doubled with
           :disable as belt-and-suspenders. -->
      <div v-if="!agentReadonly && !isActive" class="flex-none mr-sm">
        <km-btn class="width-100" :label="m.common_activate()" icon="check" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="agentReadonly" @click="doActivateVariant" />
      </div>
      <km-separator v-if="!agentReadonly" vertical tone="inverse" />
      <!-- Copy-to-new — write action. -->
      <div v-if="!agentReadonly" class="flex-none text-white mx-md">
        <km-btn :label="m.common_copyToNew()" icon="add" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="agentReadonly" @click="addVariant" />
      </div>
      <!-- Delete variant — write action. Disabled when only one variant. -->
      <div v-if="!agentReadonly" class="flex-none text-white mr-md">
        <km-btn class="mx-xs" flat :icon="&quot;delete&quot;" icon-size="16px" size="13px" :disable="agentReadonly || variantOptions?.length === 1" @click="doDeleteVariant" />
      </div>
      <prompts-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
      <km-inner-loading :showing="loading" />
    </div>
  </div>
</template>

<script>
import { computed, inject, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { notify } from '@shared/utils/notify'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

export default {
  components: { KmDropdownSelect },
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const { options: items } = useCatalogOptions('agents')
    const { draft, isDirty, updateField, updateVariantField,
            selectedVariant, activeVariant, variants, setSelectedVariant,
            createVariant, deleteVariant, activateVariant,
            save, revert } = useAgentEntityDetail()

    // Read-only signal provided by Agents/details.vue. Default to false so
    // standalone usage (e.g. tests, storybook) keeps working.
    const agentReadonlyRef = inject('agentReadonly', null)
    const agentReadonly = computed(() => Boolean(agentReadonlyRef?.value))

    return {
      m,
      draft,
      isDirty,
      updateField,
      updateVariantField,
      selectedVariant,
      activeVariant,
      variants,
      setSelectedVariant,
      createVariant: createVariant,
      deleteVariant: deleteVariant,
      activateVariant: activateVariant,
      save,
      revert,
      items,
      agentReadonly,
      loading: ref(false),
      showNewDialog: ref(false),
    }
  },
  computed: {
    isActive() {
      return this.selectedVariant == this.draft?.active_variant
    },
    variantOptions() {
      return this.draft?.variants?.map((el) => ({
        label: this.getVariantLabel(el.variant),
        value: el.variant,
        badgeLabel: el.variant == this.draft?.active_variant ? m.common_active() : '',
        badgeTone: 'brand',
        badgeIcon: 'check',
      }))
    },
    variant_description: {
      get() {
        return this.activeVariant?.value?.description
      },
      set(value) {
        this.updateVariantField('description', value)
      },
    },
    created_at() {
      if (!this.activeRowDB?.created_at) return ''
      return `${this.formatDate(this.activeRowDB.created_at)}`
    },
    modified_at() {
      if (!this.activeRowDB?.updated_at) return ''
      return `${this.formatDate(this.activeRowDB.updated_at)}`
    },
    currentRow() {
      return this.draft
    },
    route() {
      return this.$route
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.items.find((item) => item.id == this.activeRowId)
    },

    activeRowName: {
      get() {
        return this.activeRowDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    options() {
      return this.items.map((item) => ({ label: item.name, value: item }))
    },
  },
  watch: {},
  created() {},

  methods: {
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    doActivateVariant() {
      this.activateVariant()
      notify.success(m.common_variantActivated())
    },
    addVariant() {
      this.createVariant()
      notify.success(m.common_variantAdded())
    },
    doDeleteVariant() {
      this.confirm(m.common_deleteVariantConfirm(), () => this.deleteVariant())
    },

    confirm(message, callback) {
      notify.confirm({
        message,
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          callback()
          notify.success(m.common_variantDeleted())
        },
      })
    },

    deleteAgentDetail() {
      notify.confirm({
        message: m.agents_deleteAgentConfirm(),
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          this.loadingDelelete = true
          this.removeEntity(this.$route.params.id)
          this.$emit('update:closeDrawer', null)
          notify.success(m.agents_promptDeleted())
          this.navigate('/prompt-templates')
        },
      })
    },
    async openDetails(row) {
      await this.$router.push(`/prompt-templates/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async doSave() {
      this.loading = true
      await this.save()
      this.loading = false
    },
    formatDate(date) {
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
  },
}
</script>
