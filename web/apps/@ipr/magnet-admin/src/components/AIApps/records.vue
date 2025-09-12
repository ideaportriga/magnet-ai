<template lang="pug">
.col
  .row.justify-center.fit.q-gap-16.items-center(v-if="tabs.length === 0")
    .col-auto
      km-empty-state(
        @click="showNewDialog = true",
      )
  div(v-else)
      .row.q-mb-12
        .col-auto.center-flex-y
        q-space
        .col-auto.center-flex-y
          km-btn(
            label="New"
            @click="showNewDialog = true"
          ).q-mr-12
      
      VueDraggable(
        v-model="tabs"
        group="nested"
        draggable=".drag-elem"
        @Start="(row) => {isMoving = true; hovered = {}, draggedRow = row.data}",
        @End="(row) => {isMoving = false, draggedRow = null}",
      ).row.q-pb-12
        .drag-elem(v-for="item in tabs" :key="item.id")
          ai-apps-record(
              :row="item" 
              :hovered="hovered"
              :isMoving="isMoving"
              :openTabDetails="openTabDetails"
              :setInactive="() => {item.inactive = !item.inactive}"
              :removeRecord="() => {clickedRow = item.system_name; showDeleteDialog = true}"
            )
          
          VueDraggable(
            v-if="item.tab_type === 'Group'"
            :modelValue="item.children ?? []"
            @update:modelValue="item.children = $event"
            group="nested"
            draggable=".drag-elem"
            style="margin-left:36px"
          ).inner-list
            
            .drag-elem(v-for="innerItem in item.children" :key="innerItem.id")
              ai-apps-record(
                :row="innerItem" 
                :hovered="hovered"
                :isMoving="isMoving"
                :openTabDetails="openTabDetails"
                :setInactive="() => {innerItem.inactive = !innerItem.inactive}"
                :removeRecord="() => {clickedRow = [item.system_name, innerItem.system_name]; showDeleteDialog = true}"
              )
            .q-pa-xs.col-xs-12.empty-placeholder(v-if="!item.children?.length && isMoving && draggedRow.tab_type != 'Group'")  
              q-card.card-hover(bordered flat style="min-width: 400px; min-height:63px").flex.justify-center.items-center
                div +
                                 
ai-app-tabs-create-new(:showNewDialog="showNewDialog" @cancel="showNewDialog = false" v-if="showNewDialog")
km-popup-confirm(:visible="showDeleteDialog" 
      confirmButtonLabel="Delete" 
      cancelButtonLabel="Cancel" 
      notificationIcon="fas fa-triangle-exclamation"
      @confirm="deleteTab(clickedRow)",
      @cancel="showDeleteDialog = false"
)
  .row.item-center.justify-center.km-heading-7 Delete tab
  .row.text-center.justify-center You are going to delete AI Tab. Are you sure? 


</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { VueDraggable } from 'vue-draggable-plus'

export default {
  components: {
    VueDraggable
  },
  setup() {
    const { selected, visibleRows, selectedRow, ...useCollection } = useChroma('ai_apps')

    return {
      activeAIApp: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      openCreateDialog: ref(true),
      showInfo: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      visibleRows,
      selectedRow,
      selected,
      useCollection,
      searchString: ref(''),
      hovered: ref({}),
      isMoving: ref(false),
      clickedRow: ref({}),
      draggedRow: ref({})
    }
  },
  computed: {
    name: {
      get() {
        return this.$store.getters.ai_app?.name || ''
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'name', value })
      }
    },
    description: {
      get() {
        return this.$store.getters.ai_app?.description || ''
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'description', value })
      }
    },
    system_name: {
      get() {
        return this.$store.getters.ai_app?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'system_name', value })
      }
    },
    tabs: {
      get() {
        return this.$store.getters.ai_app?.tabs || []
      },
      set(value) {
        console.log('TABS', value)
        this.$store.commit('updateAIAppProperty', { key: 'tabs', value })
      }
    },
    searchedTabs: {
      get() {
        return this.tabs.filter((tab) => tab.name.toLowerCase().includes(this.searchString.toLowerCase()))
      },
      set(value) {
        this.tabs = value
      }
    },
    activeAIAppId() {
      return this.$route.params?.id
    },
    activeAIAppName() {
      return this.items?.find((item) => item?.id == this.activeAIAppId)?.name
    },
    options() {
      return this.items?.map((item) => item?.name)
    },
    loading() {
      return !this.$store?.getters?.ai_app?.id
    }
  },
  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setAIApp', newVal)
        this.tab = 'retrieve'
        this.$store.commit('clearSemanticSeacrhAnswers')
      }
    }
  },
  mounted() {
    if (this.activeAIAppId != this.$store.getters.ai_app?.id) {
      this.$store.commit('setAIApp', this.selectedRow)
      this.$store.commit('clearSemanticSeacrhAnswers')
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    openTabDetails(row) {
      if (row.tab_type === 'Group') return
      this.$store.commit('setAIAppTab', row)
      this.navigate(`${this.$route.path}/items/${row.system_name}`)
    },
    deleteTab(payload) {
      this.$store.commit('deleteAIAppTab', payload)
      this.showDeleteDialog = false
    }
  }
}
</script>

<style lang="stylus">
.gradient {
  background: linear-gradient(121.5deg, #6840C2 9.69%, #E30052 101.29%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}
.inner-list:has(.sortable-ghost)
  .empty-placeholder
    display:none;
.drag-elem
  width: 100%
.empty-placeholder
.card-hover:hover  {
  background: var(--q-background)
  cursor pointer
  border-color: var(--q-primary)
}
</style>
