<script setup lang="ts">
/**
 * Breadcrumb — semantic navigation landmark for hierarchical paths.
 *
 *   <DsBreadcrumb>
 *     <DsBreadcrumbList>
 *       <DsBreadcrumbItem>
 *         <DsBreadcrumbLink href="/">Home</DsBreadcrumbLink>
 *       </DsBreadcrumbItem>
 *       <DsBreadcrumbSeparator />
 *       <DsBreadcrumbItem>
 *         <DsBreadcrumbPage>Settings</DsBreadcrumbPage>
 *       </DsBreadcrumbItem>
 *     </DsBreadcrumbList>
 *   </DsBreadcrumb>
 */
</script>

<template>
  <nav
    class="ds-breadcrumb"
    aria-label="breadcrumb"
    data-test="ds-breadcrumb"
  >
    <slot />
  </nav>
</template>

<style>
.ds-breadcrumb {
  display: block;
  font-family: var(--ds-font-default);
  color: var(--ds-color-text-grey);
}
</style>
