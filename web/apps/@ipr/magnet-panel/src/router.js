import { createRouter, createWebHashHistory } from 'vue-router'

import LayoutTab from '@/components/LayoutTab.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { public: true },
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/pages/SignupPage.vue'),
    meta: { public: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@ui/components/auth/AuthForgotPassword.vue'),
    meta: { public: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/pages/ProfilePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile/security',
    name: 'Security',
    component: () => import('@/pages/SecurityPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/',
    name: 'Panel',
    component: LayoutTab,
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
