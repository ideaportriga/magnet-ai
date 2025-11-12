<template lang="pug">
q-dialog(v-model='popupVisible', @hide='hide')
  q-card.card-style(data-test='popup-confirm')
    q-card-section.card-section-style.q-mb-md
      .row
        .col
          .km-heading-7 {{ title }}
        .col-auto
          q-btn(icon='close', flat, dense, @click='cancel')
    q-card-section.card-section-style.q-mb-md(v-if='notificationIcon')
      .row.items-center.justify-center
        q-icon.logo-text(:name='notificationIcon', size='32px')
    q-card-section.card-section-style.q-mb-md(v-if='notification')
      km-notification-text(:notification='notification')
    q-card-section.card-section-style
      slot
    q-card-actions.card-actions-style.row.flex
      .col-auto
        km-btn(flat, :label='cancelButtonLabel', color='primary', @click='cancel', :data-test='cancelButtonLabel')
      .col
      .col-auto.q-mr-sm(v-if='confirmButtonLabel2')
        km-btn(
          :label='confirmButtonLabel2',
          @click='confirm2',
          :flat='confirmButtonType2 === "secondary" ? true : false',
          :color='confirmButtonType2 === "secondary" ? "primary" : undefined'
          :data-test='confirmButtonLabel2'
        )
      .col-auto
        km-btn(:label='confirmButtonLabel', @click='confirm' :data-test='confirmButtonLabel')

    q-inner-loading(:showing='loading')
</template>

<script>
export default {
  name: 'PopupConfirm',
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
    notification: {
      type: String,
      default: '',
    },
    notificationIcon: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
    confirmButtonLabel: {
      type: String,
      default: 'Confirm',
    },
    confirmButtonLabel2: {
      type: String,
      default: '',
    },
    confirmButtonType2: {
      type: String,
      default: 'default',
    },
    cancelButtonLabel: {
      type: String,
      default: 'Cancel',
    },
    visible: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:visible', 'cancel', 'confirm', 'confirm2'],
  data() {
    return {
      popupVisible: this.visible,
    }
  },
  watch: {
    visible(val) {
      this.popupVisible = val
    },
    popupVisible(val) {
      this.$emit('update:visible', val)
    },
  },
  methods: {
    hide() {
      this.$emit('cancel')
    },
    confirm() {
      this.$emit('confirm')
    },
    confirm2() {
      this.$emit('confirm2')
    },
    cancel() {
      this.$emit('cancel')
    },
  },
}
</script>

<style scoped>
.card-style {
  width: 676px;
  padding: 32px;
}

.card-section-style {
  padding: 0 !important;
}

.card-actions-style {
  padding: 32px 0 0 0 !important;
}

.notification {
  color: var(--q-secondary-text);
  height: 33px;
  width: 100%;
}
</style>
