<template lang="pug">
.row.q-gap-8
  template(v-for='(item, index) in data')
    div(:style='{ flex: 1 }', @mouseenter='hover = index', @mouseleave='hover = null', @click='item.action && item.action()') 
      .border-radius-12.row.items-center.justify-center.box-container(
        style='height: 90px',
        :class='`bg-${item.backgroundColor}`',
        :style='{ cursor: item.action ? "pointer" : "default" }'
      )
        .column.items-center.justify-center.q-pa-md.no-wrap.q-gap-8
          template(v-if='item.icon')
            q-icon(:name='item.icon', :color='item.iconColor', size='24px')
          template(v-else-if='item.svgIcon')
            km-icon(:name='item.svgIcon', width='20', height='20', :class='`text-${item.iconColor}`')
          template(v-else-if='item.title')
            .text-center.km-heading-4(:class='`text-${item.iconColor}`') {{ item.title }}
          .km-chart-value.full-width.text-center(:class='`text-${item.iconColor}`') {{ item?.value }}
          //q-icon.cursor-pointer.col-auto.q-pl-4(v-if='hover == index && item.action', name='fas fa-chevron-right', color='secondary', size='12px')
</template>
<script>
import { ref } from 'vue'
export default {
  props: {
    data: {
      type: Array,
      required: true,
    },
  },
  setup() {
    return {
      hover: ref(null),
    }
  },
}
</script>
<style lang="stylus" scoped>
.box-container
  transition: transform 0.3s ease-in-out;
  &:hover
    transform: translateY(-5px);
</style>
