<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const menuItems = computed(() => auth.menu);

function isActive(path) {
  return route.path.startsWith(path);
}

function go(path) {
  router.push(path);
}

async function logout() {
  await auth.logoutRemote();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar card">
      <div class="brand">
        <div class="brand-mark">TCM</div>
        <div>
          <div class="brand-title">TCM Management</div>
          <div class="brand-sub">Vue3 + Django API</div>
        </div>
      </div>

      <nav class="menu">
        <button
          v-for="item in menuItems"
          :key="item.permission_code"
          class="menu-item"
          :class="{ active: isActive(item.path) }"
          @click="go(item.path)"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="user-box">
        <div class="user-name">{{ auth.user?.real_name || auth.user?.username }}</div>
        <div class="user-role">{{ auth.user?.role_name || "No role assigned" }}</div>
        <button class="btn btn-muted" @click="logout">Logout</button>
      </div>
    </aside>

    <main class="main">
      <header class="topbar card">
        <div class="topbar-title">{{ route.name }}</div>
        <div class="topbar-tip">Permissions: {{ auth.permissions.length }}</div>
      </header>
      <section class="content">
        <RouterView />
      </section>
    </main>
  </div>
</template>
