<template lang="pug">
user-profile-page(:user-info='auth.userInfo', @save='handleSave')
</template>

<script setup>
import { defineAsyncComponent } from 'vue'
import { useAuth } from '@/pinia'

const UserProfilePage = defineAsyncComponent(() => import('@ui/components/user/UserProfilePage.vue'))

const auth = useAuth()

function handleSave(data) {
  // TODO: call PATCH /api/admin/users/{id} to update profile
  console.log('Save profile:', data)
}
</script>
