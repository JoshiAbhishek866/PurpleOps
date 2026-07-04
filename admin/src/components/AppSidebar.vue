<script setup>
import { RouterLink } from 'vue-router'
import { AppSidebarNav } from '@/components/AppSidebarNav.js'
import { useSidebarStore } from '@/stores/sidebar.js'

const sidebar = useSidebarStore()
</script>

<template>
  <CSidebar
    class="border-end"
    colorScheme="dark"
    position="fixed"
    :unfoldable="sidebar.unfoldable"
    :visible="sidebar.visible"
    @visible-change="(value) => sidebar.toggleVisible(value)"
  >
    <CSidebarHeader class="border-bottom">
      <RouterLink custom to="/" v-slot="{ href, navigate }">
        <CSidebarBrand v-bind="$attrs" as="a" :href="href" @click="navigate">
          <div class="sidebar-brand-full d-flex align-items-center">
            <span class="text-primary fw-bold fs-4">PurpleOps</span>
          </div>
          <div class="sidebar-brand-narrow"><span class="text-primary fw-bold fs-5">HS</span></div>
        </CSidebarBrand>
      </RouterLink>
      <CCloseButton class="d-lg-none" dark @click="sidebar.toggleVisible()" />
    </CSidebarHeader>
    <AppSidebarNav />
    <CSidebarFooter class="border-top d-none d-lg-flex"
      ><CSidebarToggler @click="sidebar.toggleUnfoldable()"
    /></CSidebarFooter>
  </CSidebar>
</template>

<style scoped>
/* Clean Sidebar Navigation - Matching Reference Image */

/* Hide all icons */
:deep(.nav-icon) {
  display: none !important;
}

/* Section Headers (CNavTitle) - Left aligned, no indentation */
:deep(.nav-title) {
  padding-left: 1rem !important;
  padding-right: 1rem !important;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.5rem;
  margin-bottom: 0.25rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Level 1: Main navigation items - Left aligned */
:deep(.sidebar-nav > .nav-item > .nav-link),
:deep(.sidebar-nav > .nav-group > .nav-link) {
  padding-left: 1rem !important;
  padding-right: 1rem !important;
  font-size: 0.9375rem;
  font-weight: 400;
}

/* Level 2: Sub-items - Indented to the right */
:deep(.nav-group .nav-group-items > .nav-item > .nav-link) {
  padding-left: 2.5rem !important;
  padding-right: 1rem !important;
  font-size: 0.875rem;
  font-weight: 300;
}

/* Level 3: Nested groups - Slightly more indented */
:deep(.nav-group .nav-group-items .nav-group > .nav-link) {
  padding-left: 2.5rem !important;
  padding-right: 1rem !important;
  font-size: 0.875rem;
  font-weight: 400;
}

/* Level 4: Sub-sub-items - Maximum indentation */
:deep(.nav-group .nav-group-items .nav-group .nav-group-items > .nav-item > .nav-link) {
  padding-left: 3.5rem !important;
  padding-right: 1rem !important;
  font-size: 0.8125rem;
  font-weight: 300;
}

/* Clean spacing */
:deep(.nav-item),
:deep(.nav-group) {
  margin-bottom: 0.125rem;
}

/* Hover effect - subtle */
:deep(.nav-link:hover) {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0;
}

/* Active state - clean highlight like reference */
:deep(.nav-link.active) {
  background-color: rgba(var(--cui-primary-rgb), 0.15);
  /* border-left: 3px solid var(--cui-primary); */
  font-weight: 500;
}

/* Remove default borders and extra spacing */
:deep(.nav-group .nav-group-items) {
  padding-top: 0;
  padding-bottom: 0;
}

/* Clean toggle icon for groups */
:deep(.nav-group-toggle::after) {
  margin-left: auto;
}

/* Adjust vertical spacing */
:deep(.nav-link) {
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
  border-radius: 0;
}
</style>
