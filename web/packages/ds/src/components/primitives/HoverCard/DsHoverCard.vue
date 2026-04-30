<script setup lang="ts">
/**
 * HoverCard — peek preview shown when hovering / focusing the trigger.
 *
 *   <DsHoverCard>
 *     <DsHoverCardTrigger>@user</DsHoverCardTrigger>
 *     <DsHoverCardContent>
 *       <p>User profile preview…</p>
 *     </DsHoverCardContent>
 *   </DsHoverCard>
 */

import {
  HoverCardRoot,
  type HoverCardRootEmits,
  type HoverCardRootProps,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<HoverCardRootProps>()
const emits = defineEmits<HoverCardRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <HoverCardRoot v-slot="slotProps" v-bind="forwarded">
    <slot v-bind="slotProps" />
  </HoverCardRoot>
</template>
