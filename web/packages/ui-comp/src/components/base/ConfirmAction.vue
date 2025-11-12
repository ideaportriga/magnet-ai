<template lang="pug">
q-dialog(ref='dialog', @hide='onDialogHide')
  q-card.q-dialog-plugin
    .column.bg-white.panel-borders.q-px-lg.q-pt-md.q-pb-lg
      .col.km-body.q-mx-md Move this promotion to Cancelled status?
      .col.q-mt-md
        .row.justify-evenly
          .col-auto
            km-btn(label='Go back', secondary, @click='onCancelClick')
          .col-auto
            km-btn(label='Yes, cancel promo', @click='onOKClick')
</template>

<script>
export default {
  props: {
    // ...your custom props
  },

  emits: [
    // REQUIRED
    'ok',
    'hide',
  ],

  methods: {
    // following method is REQUIRED
    // (don't change its name --> "show")
    show() {
      this.$refs.dialog.show()
    },

    // following method is REQUIRED
    // (don't change its name --> "hide")
    hide() {
      this.$refs.dialog.hide()
    },

    onDialogHide() {
      // required to be emitted
      // when QDialog emits "hide" event
      this.$emit('hide')
    },

    onOKClick() {
      // on OK, it is REQUIRED to
      // emit "ok" event (with optional payload)
      // before hiding the QDialog
      this.$emit('ok')
      // or with payload: this.$emit('ok', { ... })

      // then hiding dialog
      this.hide()
    },

    onCancelClick() {
      // we just need to hide the dialog
      this.hide()
    },
  },
}
</script>
